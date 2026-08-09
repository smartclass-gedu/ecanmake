# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

from datetime import datetime
import frappe
from frappe.model.document import Document


class AssetLifecycle(Document):
	def validate(self):
		"""Calculate current book value based on depreciation"""
		self.calculate_book_value()

	def calculate_book_value(self):
		"""
		Compute current_book_value = original_cost − (original_cost × depreciation_rate/100 × years_elapsed)
		"""
		if not self.original_cost or not self.depreciation_rate:
			self.current_book_value = self.original_cost or 0
			return

		# Get equipment's acquisition date
		equipment_doc = frappe.get_doc("Lab Equipment", self.equipment)
		if not equipment_doc.acquisition_date:
			self.current_book_value = self.original_cost
			return

		# Calculate years elapsed since acquisition
		from datetime import date
		acquisition_date = equipment_doc.acquisition_date
		if isinstance(acquisition_date, str):
			acquisition_date = datetime.strptime(acquisition_date, "%Y-%m-%d").date()

		today = date.today()
		years_elapsed = (today - acquisition_date).days / 365.25

		# Calculate depreciation
		annual_depreciation = self.original_cost * (self.depreciation_rate / 100)
		total_depreciation = annual_depreciation * years_elapsed

		# Book value = original cost - accumulated depreciation
		self.current_book_value = max(0, self.original_cost - total_depreciation)
