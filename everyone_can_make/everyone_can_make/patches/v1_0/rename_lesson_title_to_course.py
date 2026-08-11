# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
	"""Rename lesson_title field to course on Atomic Learning doctype"""
	if not frappe.db.table_has_column("Atomic Learning", "lesson_title"):
		return
	frappe.reload_doc("everyone_can_make", "doctype", "atomic_learning")
	rename_field("Atomic Learning", "lesson_title", "course")
