"""
Autoname utility for Course Lesson doctype.
Generates hierarchical shorthand names: COURSE-CHAPTER-LESSON
"""

import frappe


def generate_course_lesson_shorthand(course_lesson_doc):
	"""
	Generate a shorthand name for Course Lesson based on hierarchy.
	Format: {COURSE_CODE}-{CHAPTER_NUM}-{LESSON_NUM}

	Example: "Python-01-L03" for Python course, chapter 1, lesson 3

	Args:
		course_lesson_doc: Course Lesson document with chapter and course fields

	Returns:
		str: Shorthand name
	"""
	try:
		# Get chapter and course info
		chapter = frappe.get_doc("Course Chapter", course_lesson_doc.chapter)
		course = frappe.get_doc("LMS Course", chapter.course)

		# Generate course code (first 3 letters of course name or custom code)
		course_code = (
			course.get("course_code")
			or course.name[:3].upper()
			or "CRS"
		)

		# Get chapter number (ordinal in course)
		chapters = frappe.get_list(
			"Course Chapter",
			filters={"course": chapter.course},
			fields=["name"],
			order_by="creation asc"
		)
		chapter_num = next(
			(i + 1 for i, ch in enumerate(chapters) if ch.name == course_lesson_doc.chapter),
			1
		)

		# Get lesson number (ordinal in chapter)
		lessons = frappe.get_list(
			"Course Lesson",
			filters={"chapter": course_lesson_doc.chapter},
			fields=["name"],
			order_by="creation asc"
		)
		lesson_num = next(
			(i + 1 for i, les in enumerate(lessons) if les.name == course_lesson_doc.name),
			1
		)

		# Generate shorthand
		shorthand = f"{course_code}-{chapter_num:02d}-L{lesson_num:02d}"
		return shorthand

	except Exception as e:
		frappe.log_error(f"Error generating Course Lesson shorthand: {str(e)}")
		return None


def on_course_lesson_before_insert(doc, method):
	"""
	Hook called before Course Lesson insert.
	Auto-generates a shorthand name if title is empty or contains placeholder text.
	"""
	# Only generate if title is missing or is placeholder
	if not doc.title or doc.title.strip().lower() in ["untitled", "lesson", ""]:
		shorthand = generate_course_lesson_shorthand(doc)
		if shorthand:
			doc.name = shorthand
			doc.title = shorthand  # Also set title to the shorthand
			frappe.msgprint(f"Auto-named lesson: {shorthand}", alert=True)


def on_course_lesson_before_save(doc, method):
	"""
	Hook called before Course Lesson save.
	Updates name if title changed significantly.
	"""
	# Only rename if this is a new doc being created
	if doc.is_new():
		on_course_lesson_before_insert(doc, method)


def rename_untitled_lessons():
	"""
	Migration function to rename all existing untitled lessons.
	Run this once to fix existing records.

	Usage:
		frappe.call({
			'method': 'everyone_can_make.course_lesson_utils.rename_untitled_lessons'
		})

	Or from console:
		bench execute everyone_can_make.course_lesson_utils.rename_untitled_lessons
	"""
	# Get all Course Lessons that are untitled or have placeholder titles
	untitled_lessons = frappe.get_list(
		"Course Lesson",
		filters=[
			["title", "in", ["", "Untitled", "Lesson", "untitled"]],
		],
		fields=["name", "chapter", "title"]
	)

	total = len(untitled_lessons)
	renamed = 0
	errors = []

	frappe.log_error(f"Starting to rename {total} untitled lessons")

	for lesson_data in untitled_lessons:
		try:
			doc = frappe.get_doc("Course Lesson", lesson_data.name)
			shorthand = generate_course_lesson_shorthand(doc)

			if shorthand and shorthand != doc.name:
				# Check if new name already exists
				if frappe.db.exists("Course Lesson", shorthand):
					shorthand = f"{shorthand}-{doc.creation.timestamp():.0f}"

				# Rename the document
				frappe.rename_doc("Course Lesson", doc.name, shorthand, merge=False)
				doc.title = shorthand
				doc.save()
				renamed += 1
				frappe.msgprint(f"Renamed {doc.name} → {shorthand}")

		except Exception as e:
			error_msg = f"Error renaming {lesson_data.name}: {str(e)}"
			frappe.log_error(error_msg)
			errors.append(error_msg)

	summary = f"\n✓ Renamed {renamed}/{total} lessons"
	if errors:
		summary += f"\n✗ Errors: {len(errors)}"
		for err in errors[:5]:  # Show first 5 errors
			summary += f"\n  - {err}"

	frappe.msgprint(summary, alert=True)
	return {"renamed": renamed, "total": total, "errors": errors}
