from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from officeaid.auth import (is_admin, is_admin_or_manager,
    is_admin_manager_or_pm, is_authenticated, is_not_authenticated)

# 4-tuples of (section id, label, URL name, user permission test function)
SECTIONS = (
    ('login',      'Login',      'login',           is_not_authenticated),
    ('timesheets', 'Timesheets', 'timesheet_index', is_authenticated),
    ('activities', 'Activities', 'activity_list',   is_authenticated),
    ('manage',     'Manage',     'job_list',        is_authenticated),
    ('invoices',   'Invoices',   'invoice_list',    is_admin_or_manager),
    ('reports',    'Reports',    'report_list',     is_authenticated),
    ('logout',     'Logout',     'logout',          is_authenticated),
)

# A dict mapping section ids to 4-tuples of (page id, label, URL name, user permission test function)
PAGES = {
    'timesheets': (
        ('bulk_approval', 'Bulk Approval', 'bulk_approval', is_admin),
    ),
    'manage': (
        ('clients',        'Clients',        'client_list',        is_authenticated),
        ('contacts',       'Contacts',       'contact_list',       is_authenticated),
        ('jobs',           'Jobs',           'job_list',           is_authenticated),
        ('users',          'Users',          'user_list',          is_admin_or_manager),
        ('task_types',     'Task Types',     'task_type_list',     is_admin_or_manager),
        ('expense_types',  'Expense Types',  'expense_type_list',  is_admin_or_manager),
        ('activity_types', 'Activity Types', 'activity_type_list', is_admin_or_manager),
        ('artifact_types', 'Artifact Types', 'artifact_type_list', is_admin_or_manager),
    ),
    'invoices': (
        ('invoices',        'Invoices',        'invoice_list',    is_admin_or_manager),
        ('create_invoices', 'Create Invoices', 'create_invoices', is_admin_or_manager),
    ),
    'reports': (
        ('job_reports',            'Job Reports',       'job_report_list',        is_admin_or_manager),
        ('timesheet_reports',      'Timesheet Reports', 'timesheet_report_list',  is_authenticated),
        ('user_report',            'Users',             'user_report',            is_authenticated),
        ('annual_leave_report',    'Annual Leave',      'annual_leave_report',    is_authenticated),
        ('client_report',          'Clients',           'client_report',          is_authenticated),
        ('invoiced_work_report',   'Invoiced Work',     'invoiced_work_report',   is_admin_or_manager),
        ('uninvoiced_work_report', 'Uninvoiced Work',   'uninvoiced_work_report', is_admin_or_manager),
        ('sql_reports',            'SQL Reports',       'sql_report_list',        is_authenticated),
    ),
}

def build_menu_items(user, active_section_id=None, active_page_id=None,
        item_template='<li %(id)s%(class)s><a href="%(url)s">%(label)s</a></li>',
        item_id_prefix='nav_'):
    """
    Builds section menu items and related page submenu items which the
    logged-in User has permission to see.

    user
        The logged-in user.

    active_section_id
        The id of a section to be marked as active and have its page
        submenu displayed.

    active_page_id
        The id of the a to be marked as active in the dispalyed page
        submenu.

    item template
        An HTML template for each item produced - must contain named
        placeholders for ``id`` and ``class`` attributes, and for
        ``url`` and ``label`` values.

    item_id_prefix
        A prefix to be applied to all item ``id`` attributes.
    """
    section_items, page_items = [], []

    for (section_id, label, url_name, user_permission_test) in SECTIONS:
        if user_permission_test and not user_permission_test(user):
            continue
        item_class = ''
        if active_section_id and section_id == active_section_id:
            item_class = ' class="active"'
        section_items.append(item_template % {
            'id': 'id="%s%s"' % (item_id_prefix, section_id),
            'class': item_class,
            'url': reverse(url_name),
            'label': escape(label)
        })

    if PAGES.has_key(active_section_id):
        for (page_id, label, url_name, user_permission_test) in PAGES[active_section_id]:
            if user_permission_test and not user_permission_test(user):
                continue
            item_class = ''
            if active_page_id and page_id == active_page_id:
                item_class = ' class="active"'
            page_items.append(item_template %  {
                'id': 'id="%s%s"' % (item_id_prefix, page_id),
                'class': item_class,
                'url': reverse(url_name),
                'label': escape(label)
            })

    for i, item in enumerate(section_items):
        section_items[i] = mark_safe(item)

    for i, item in enumerate(page_items):
        page_items[i] = mark_safe(item)

    return (section_items, page_items)
