# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Instructor(Document):
	def validate(self):
		"""Enforce that instructor has at least one skill domain certified"""
		if not self.skill_domains or len(self.skill_domains) == 0:
			frappe.throw("Instructor must have at least one certified skill domain")
