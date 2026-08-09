# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document


class ResourceBooking(Document):
	def before_insert(self):
		"""Set created_date and booking_made_by before first insert"""
		self.created_date = frappe.utils.today()
		self.booking_made_by = frappe.session.user

	def validate(self):
		"""Validate availability and calculate costs"""
		self.check_availability()
		self.calculate_costs()
		self.calculate_instructor_hours()
		# Update School rollups if this is a school booking
		if self.booking_type == "School" and self.school:
			school_doc = frappe.get_doc("School", self.school)
			school_doc.update_rollups()

	def check_availability(self):
		"""
		Check if equipment and instructor are available during the booking window.
		Block if equipment is overbooked past max_concurrent_users,
		or if instructor has conflicts.
		"""
		if not self.start_datetime or not self.end_datetime or not self.location:
			return

		start_dt = self.start_datetime
		end_dt = self.end_datetime

		# Check each equipment item for availability
		if self.resources:
			for row in self.resources:
				if not row.equipment_item:
					continue

				# Get equipment's max_concurrent_users
				equipment = frappe.get_doc("Lab Equipment", row.equipment_item)
				max_concurrent = equipment.max_concurrent_users or 1

				# Count overlapping non-cancelled bookings for this equipment at this location
				overlapping = frappe.db.count(
					"Resource Booking",
					filters={
						"name": ("!=", self.name),
						"status": ("!=", "Cancelled"),
						"location": self.location,
					}
				)

				# Check if any resource rows overlap with this equipment
				conflicting_bookings = frappe.get_all(
					"Resource Booking",
					filters={
						"name": ("!=", self.name),
						"status": ("!=", "Cancelled"),
						"location": self.location,
					},
					fields=["name", "start_datetime", "end_datetime"]
				)

				conflict_count = 0
				for booking in conflicting_bookings:
					# Check for time overlap
					booking_start = booking.get("start_datetime")
					booking_end = booking.get("end_datetime")
					if booking_start < end_dt and booking_end > start_dt:
						# Times overlap — check if this equipment is in that booking
						if frappe.db.exists(
							"Booking Resource",
							{
								"parent": booking.get("name"),
								"equipment_item": row.equipment_item
							}
						):
							conflict_count += 1

				if conflict_count >= max_concurrent:
					frappe.throw(
						f"Equipment '{row.equipment_item}' is already booked for "
						f"{conflict_count} concurrent sessions during this time window. "
						f"Maximum concurrent users: {max_concurrent}"
					)

		# Check instructor availability if assigned
		if self.instructor:
			conflicting_sessions = frappe.get_all(
				"Instructor Session",
				filters={
					"instructor": self.instructor,
					"status": ("!=", "Cancelled"),
				},
				fields=["name", "start_time", "end_time"]
			)

			for session in conflicting_sessions:
				session_start = session.get("start_time")
				session_end = session.get("end_time")
				if session_start < end_dt and session_end > start_dt:
					frappe.throw(
						f"Instructor '{self.instructor}' has a conflicting session "
						f"({session.get('name')}) during this time window."
					)

			# Also check other Resource Booking conflicts for same instructor
			conflicting_bookings = frappe.get_all(
				"Resource Booking",
				filters={
					"name": ("!=", self.name),
					"instructor": self.instructor,
					"status": ("!=", "Cancelled"),
				},
				fields=["name", "start_datetime", "end_datetime"]
			)

			for booking in conflicting_bookings:
				booking_start = booking.get("start_datetime")
				booking_end = booking.get("end_datetime")
				if booking_start < end_dt and booking_end > start_dt:
					frappe.throw(
						f"Instructor '{self.instructor}' is already booked for "
						f"Resource Booking {booking.get('name')} during this time window."
					)

	def calculate_instructor_hours(self):
		"""Compute instructor_hours from resources (sum of hours_needed)"""
		self.instructor_hours = sum(
			row.hours_needed or 0 for row in (self.resources or [])
		)

	def calculate_costs(self):
		"""Calculate equipment_cost, instructor_cost, and total_cost"""
		# Equipment cost = sum of subtotals
		self.equipment_cost = sum(
			(row.hours_needed or 0) * (row.hourly_rate or 0)
			for row in (self.resources or [])
		)

		# Instructor cost
		self.instructor_cost = 0
		if self.instructor:
			instructor_doc = frappe.get_doc("Instructor", self.instructor)
			hours = self.calculate_instructor_hours()
			if instructor_doc.flat_rate_per_session:
				self.instructor_cost = instructor_doc.flat_rate_per_session
			else:
				self.instructor_cost = (instructor_doc.hourly_rate or 0) * hours

		# Total cost with discount
		subtotal = self.equipment_cost + self.instructor_cost + (self.material_cost or 0)
		discount_amount = subtotal * ((self.discount_percent or 0) / 100)
		self.total_cost = subtotal - discount_amount
