import frappe


def execute():
	"""Remove Course Outcome and Outcome Skill doctypes."""
	frappe.delete_doc("DocType", "Course Outcome", force=True, ignore_missing=True)
	frappe.delete_doc("DocType", "Outcome Skill", force=True, ignore_missing=True)
