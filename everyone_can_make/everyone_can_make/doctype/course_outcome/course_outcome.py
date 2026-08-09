# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CourseOutcome(Document):
	def validate(self):
		"""Recalculate total_hours based on linked lessons"""
		self.calculate_total_hours()

	def calculate_total_hours(self):
		"""Sum up duration from all lessons in this outcome"""
		total_minutes = 0
		if self.lessons:
			for row in self.lessons:
				if row.duration_override and row.duration_override > 0:
					# Use override if provided
					total_minutes += row.duration_override
				else:
					# Fetch lesson's estimated_duration_minutes
					lesson_doc = frappe.get_doc("Atomic Learning", row.lesson)
					if hasattr(lesson_doc, "estimated_duration_minutes") and lesson_doc.estimated_duration_minutes:
						total_minutes += lesson_doc.estimated_duration_minutes

		# Convert minutes to hours
		self.total_hours = round(total_minutes / 60, 2)
