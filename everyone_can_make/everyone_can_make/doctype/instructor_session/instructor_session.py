# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document


class InstructorSession(Document):
	def validate(self):
		"""Calculate duration_hours and cost"""
		self.calculate_duration()
		self.calculate_cost()

	def calculate_duration(self):
		"""Compute duration_hours from start_time and end_time"""
		if self.start_time and self.end_time:
			# Parse if they're strings
			if isinstance(self.start_time, str):
				start = datetime.fromisoformat(self.start_time)
			else:
				start = self.start_time

			if isinstance(self.end_time, str):
				end = datetime.fromisoformat(self.end_time)
			else:
				end = self.end_time

			delta = end - start
			self.duration_hours = round(delta.total_seconds() / 3600, 2)

	def calculate_cost(self):
		"""Compute cost = instructor.hourly_rate × duration_hours"""
		self.cost = 0
		if self.instructor and self.duration_hours:
			instructor_doc = frappe.get_doc("Instructor", self.instructor)
			self.cost = (instructor_doc.hourly_rate or 0) * self.duration_hours
