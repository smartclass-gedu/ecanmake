"""
Patch: Rename Course Lessons with auto-generated shorthand names.
Applies hierarchical naming: COURSE-CHAPTER-LESSON to all existing lessons.

This patch:
1. Identifies all untitled or improperly named Course Lessons
2. Generates shorthand names based on course-chapter hierarchy
3. Renames the documents safely, checking for conflicts
4. Updates titles to match the new shorthand names
"""

import frappe
from everyone_can_make.course_lesson_utils import rename_untitled_lessons


def execute():
	"""
	Execute the migration to rename Course Lessons.
	Called automatically during `bench migrate`.
	"""
	frappe.msgprint("Starting Course Lesson rename migration...", alert=True)
	result = rename_untitled_lessons()
	frappe.msgprint(
		f"Migration complete: Renamed {result['renamed']}/{result['total']} lessons",
		alert=True
	)
