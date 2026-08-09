# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class School(Document):
	def update_rollups(self):
		"""
		Recompute total_bookings, total_students_served, total_spent
		from linked Resource Booking records (called from Resource Booking controller)
		"""
		# Count total bookings for this school
		self.total_bookings = frappe.db.count(
			"Resource Booking",
			{"school": self.name, "status": ("!=", "Cancelled")}
		)

		# Sum total students served (school_group_size from all bookings)
		bookings = frappe.get_all(
			"Resource Booking",
			filters={"school": self.name, "status": ("!=", "Cancelled")},
			fields=["school_group_size"]
		)
		self.total_students_served = sum(
			booking.get("school_group_size") or 0 for booking in bookings
		)

		# Sum total spent (total_cost from all bookings)
		self.total_spent = frappe.db.sum(
			"Resource Booking",
			"total_cost",
			{"school": self.name, "status": ("!=", "Cancelled")}
		) or 0

		self.db_update()
