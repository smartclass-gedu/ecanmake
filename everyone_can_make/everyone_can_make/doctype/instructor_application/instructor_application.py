# Copyright (c) 2026, Maker Murtaza and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InstructorApplication(Document):
	def before_insert(self):
		"""Stamp the submission time."""
		if not self.applied_on:
			self.applied_on = frappe.utils.now()

	def validate(self):
		"""Block a second open application for the same email, and disallow gmail.com addresses."""
		if not self.email:
			return

		if self.email.strip().lower().endswith("@gmail.com"):
			frappe.throw("Please use a non-Gmail email address to apply.")

		duplicate = frappe.db.exists(
			"Instructor Application",
			{
				"email": self.email,
				"workflow_state": ["not in", ["Rejected"]],
				"name": ["!=", self.name or ""],
			},
		)
		if duplicate:
			frappe.throw(
				f"An application from {self.email} is already {self.workflow_state or 'in progress'} ({duplicate})."
			)

	def on_update(self):
		"""React to workflow state transitions made after insert."""
		if not self.has_value_changed("workflow_state"):
			return

		if self.workflow_state == "Approved":
			self.approve()
		elif self.workflow_state == "Rejected":
			self.reject()

	def approve(self):
		"""Create the User + Instructor records and notify the applicant."""
		if self.linked_instructor:
			return  # already processed

		if frappe.db.exists("Instructor", {"email": self.email}):
			frappe.throw(f"An Instructor record already exists for {self.email}")

		user = self._get_or_create_user()
		instructor = self._create_instructor(user)

		self.db_set("linked_instructor", instructor.name)
		self.db_set("reviewed_by", frappe.session.user)

		self._send_notification(
			subject="Welcome to Everyone Can Make - Instructor Application Approved",
			message=self._approval_message(),
		)

	def reject(self):
		self.db_set("reviewed_by", frappe.session.user)
		self._send_notification(
			subject="Everyone Can Make - Instructor Application Update",
			message=self._rejection_message(),
		)

	def _get_or_create_user(self):
		if frappe.db.exists("User", self.email):
			user = frappe.get_doc("User", self.email)
		else:
			name_parts = (self.full_name or self.email).split(" ", 1)
			user = frappe.new_doc("User")
			user.email = self.email
			user.first_name = name_parts[0]
			user.last_name = name_parts[1] if len(name_parts) > 1 else ""
			user.user_type = "Website User"
			user.send_welcome_email = 1
			user.insert(ignore_permissions=True)

		if not frappe.db.exists("Has Role", {"parent": user.name, "role": "Instructor"}):
			user.add_roles("Instructor")

		return user

	def _create_instructor(self, user):
		instructor = frappe.new_doc("Instructor")
		instructor.user_link = user.name
		instructor.school = self.school
		instructor.primary_location = self.preferred_lab_location

		for row in self.skill_domains:
			instructor.append(
				"skill_domains",
				{
					"skill_domain": row.skill_domain,
					"years_experience": row.years_of_experience,
				},
			)

		instructor.insert(ignore_permissions=True)
		return instructor

	def _send_notification(self, subject, message):
		frappe.sendmail(recipients=[self.email], subject=subject, message=message, now=False)

	def _approval_message(self):
		domains = "".join(f"<li>{row.skill_domain}</li>" for row in self.skill_domains)
		return f"""
			<p>Hi {self.full_name},</p>
			<p>Congratulations! Your application to become an Instructor at Everyone Can Make has been approved.</p>
			<p><strong>Your approved skill domains:</strong></p>
			<ul>{domains}</ul>
			<p>An account has been created for you at {self.email}. Check your inbox for login instructions,
			then complete your Instructor profile (availability, rates, certifications).</p>
			<p>Welcome aboard!<br>The Everyone Can Make Team</p>
		"""

	def _rejection_message(self):
		notes = f"<p><strong>Feedback:</strong><br>{self.review_notes}</p>" if self.review_notes else ""
		return f"""
			<p>Hi {self.full_name},</p>
			<p>Thank you for applying to become an Instructor at Everyone Can Make. After review, we're unable to
			move forward with your application at this time.</p>
			{notes}
			<p>You're welcome to reapply in the future. If you have questions, just reply to this email.</p>
			<p>The Everyone Can Make Team</p>
		"""
