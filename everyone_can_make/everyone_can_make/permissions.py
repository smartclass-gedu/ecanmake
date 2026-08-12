# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

import frappe
from frappe.permissions import has_permission as default_has_permission


def _is_admin_user(user=None):
	"""Check if the user is an admin (System Manager or Administrator)"""
	if not user:
		user = frappe.session.user

	return user in ("Administrator",) or frappe.db.get_value(
		"User", user, "user_type"
	) == "Administrator" or has_role(user, "System Manager")


def has_role(user, role_name):
	"""Check if user has a specific role"""
	if not user:
		user = frappe.session.user
	return frappe.db.get_value(
		"Has Role",
		{"parent": user, "role": role_name}
	) is not None


# ============================================================================
# COURSE OUTCOME PERMISSIONS
# ============================================================================

def course_outcome_has_permission(doc, perm_type="read", user=None, raise_exception=False):
	"""
	Instructors can only view/edit courses they created (owner).
	Admins have full access.
	"""
	if not user:
		user = frappe.session.user

	# Admin always has permission
	if _is_admin_user(user):
		return True

	# For instructors: only owner (creator) can access
	if perm_type in ("read", "write"):
		if doc.owner == user:
			return True

	# Deny access for non-owners
	if raise_exception:
		frappe.throw(
			f"You do not have permission to {perm_type} this Course Outcome. "
			f"Only the creator can access it."
		)

	return False


def get_course_outcome_permission_query_conditions(user):
	"""
	Return SQL condition to filter Course Outcomes visible to the user.
	Instructors only see courses they created (owner = user).
	Admins see all.
	"""
	if _is_admin_user(user):
		return None  # No restriction for admins

	# For instructors, restrict to their own created courses
	return f"`tabCourse Outcome`.`owner` = '{frappe.db.escape(user)}'"


# ============================================================================
# LMS COURSE PERMISSIONS
# ============================================================================

def course_has_permission(doc, perm_type="read", user=None, raise_exception=False):
	"""
	Instructors can only view/edit LMS Courses they created (owner).
	Admins have full access.
	"""
	if not user:
		user = frappe.session.user

	# Admin always has permission
	if _is_admin_user(user):
		return True

	# For instructors: only owner (creator) can access
	if perm_type in ("read", "write"):
		if doc.owner == user:
			return True

	# Deny access for non-owners
	if raise_exception:
		frappe.throw(
			f"You do not have permission to {perm_type} this Course. "
			f"Only the creator can access it."
		)

	return False


def get_course_permission_query_conditions(user):
	"""
	Return SQL condition to filter LMS Courses visible to the user.
	Instructors only see courses they created (owner = user).
	Admins see all.
	"""
	if _is_admin_user(user):
		return None  # No restriction for admins

	# For instructors, restrict to their own created courses
	return f"`tabLMS Course`.`owner` = '{frappe.db.escape(user)}'"


# ============================================================================
# SCHOOL PERMISSIONS
# ============================================================================

def school_has_permission(doc, perm_type="read", user=None, raise_exception=False):
	"""
	Instructors can only view schools they are assigned to (linked via Instructor.school field).
	Admins have full access.
	"""
	if not user:
		user = frappe.session.user

	# Admin always has permission
	if _is_admin_user(user):
		return True

	# Get the instructor record for this user (if any)
	instructor_name = frappe.db.get_value("Instructor", {"user_link": user})

	if not instructor_name:
		# User is not an instructor, deny access
		if raise_exception:
			frappe.throw("Only instructors can access schools.")
		return False

	# Get the school linked to this instructor
	instructor_school = frappe.db.get_value("Instructor", instructor_name, "school")

	# If instructor has no school (freelancer), they can't access any school record
	if not instructor_school:
		if raise_exception:
			frappe.throw("You are not assigned to any school.")
		return False

	# Allow access only if the school matches their assigned school
	if perm_type in ("read", "write"):
		if doc.name == instructor_school:
			return True

	# Deny access for schools they're not assigned to
	if raise_exception:
		frappe.throw(
			f"You do not have permission to {perm_type} this school. "
			f"You can only access your assigned school."
		)

	return False


def get_school_permission_query_conditions(user):
	"""
	Return SQL condition to filter Schools visible to the user.
	Instructors only see the school they are linked to.
	Admins see all.
	"""
	if _is_admin_user(user):
		return None  # No restriction for admins

	# Get the instructor record for this user
	instructor_name = frappe.db.get_value("Instructor", {"user_link": user})

	if not instructor_name:
		# User is not an instructor, return condition that matches nothing
		return "`tabSchool`.`name` = ''  -- User is not an instructor"

	# Get the school linked to this instructor
	instructor_school = frappe.db.get_value("Instructor", instructor_name, "school")

	if not instructor_school:
		# Freelancer (no school assigned), restrict to non-existent schools
		return "`tabSchool`.`name` = ''  -- Freelancer with no assigned school"

	# Restrict to their assigned school
	return f"`tabSchool`.`name` = '{frappe.db.escape(instructor_school)}'"


# ============================================================================
# INSTRUCTOR PERMISSIONS
# ============================================================================

def instructor_has_permission(doc, perm_type="read", user=None, raise_exception=False):
	"""
	Instructors can only view/edit their own Instructor record.
	Admins have full access.
	"""
	if not user:
		user = frappe.session.user

	# Admin always has permission
	if _is_admin_user(user):
		return True

	# For instructors: only allow read/write on their own record
	if perm_type in ("read", "write"):
		if doc.user_link == user:
			return True

	# Deny access for other instructors' records
	if raise_exception:
		frappe.throw(
			f"You do not have permission to {perm_type} this Instructor record. "
			f"You can only manage your own record."
		)

	return False
