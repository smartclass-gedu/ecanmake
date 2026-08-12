/**
 * Course Lesson Auto-Naming UI Enhancement
 *
 * Shows helpful hints to users when creating Course Lessons without a title.
 * Demonstrates the auto-naming feature and how to use it.
 */

frappe.ui.form.on('Course Lesson', {
	/**
	 * On form load, show info about auto-naming feature
	 */
	setup: function(frm) {
		if (frm.is_new()) {
			// Add custom help text for new lessons
			frm.set_df_property('title', 'description',
				'Leave blank or enter "Lesson" to use auto-generated shorthand name<br/>' +
				'<strong>Format:</strong> COURSE-CHAPTER-LESSON (e.g., Python-01-L03)<br/>' +
				'Or enter a custom title for this lesson.'
			);
		}
	},

	/**
	 * Show preview of generated shorthand when chapter is selected
	 */
	chapter: function(frm) {
		if (frm.doc.chapter) {
			// Fetch chapter to get course info
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Course Chapter',
					name: frm.doc.chapter
				},
				callback: function(r) {
					if (r.message) {
						const chapter = r.message;
						const course_name = chapter.course;

						// Show preview message
						frappe.msgprint({
							title: 'Auto-Naming Preview',
							message: `This lesson will be automatically named as:<br/>` +
									`<strong>${course_name.substring(0, 3).toUpperCase()}-01-L01</strong><br/><br/>` +
									`(Exact chapter/lesson numbers will be determined when saved)`,
							indicator: 'blue'
						});

						// Update description with course info
						frm.set_df_property('title', 'description',
							`Course: <strong>${course_name}</strong><br/>` +
							'Leave blank or enter "Lesson" to use shorthand: <strong>COURSE-CHAPTER-LESSON</strong><br/>' +
							'Or enter a custom title for this lesson.'
						);
					}
				}
			});
		}
	},

	/**
	 * Validate title on save
	 */
	before_save: function(frm) {
		// Show what will happen
		if (!frm.doc.title || frm.doc.title.toLowerCase().trim() === 'lesson') {
			frappe.msgprint({
				title: 'Auto-Naming Active',
				message: 'Your lesson will be automatically named with a shorthand. ' +
						'The title will be set to match the generated name.',
				indicator: 'green'
			});
		}
	}
});

/**
 * Add button to rename all lessons (accessible from list view)
 */
frappe.listview_settings['Course Lesson'] = {
	add_fields: ['title', 'chapter', 'course'],

	onload: function(listview) {
		// Add a custom action button
		listview.page.add_action_item('Rename Untitled Lessons', function() {
			if (!frappe.user.has_role('System Manager')) {
				frappe.msgprint('You need System Manager role to rename lessons.');
				return;
			}

			frappe.confirm('Rename all untitled lessons with auto-generated shorthand names?<br/>' +
						   'This cannot be undone.',
				function() {
					frappe.call({
						method: 'everyone_can_make.course_lesson_utils.rename_untitled_lessons',
						callback: function(r) {
							frappe.msgprint(
								`Renamed ${r.message.renamed}/${r.message.total} lessons`,
								'Success'
							);
							listview.refresh();
						}
					});
				}
			);
		});
	}
};
