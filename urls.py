from django.conf.urls.defaults import *

TIMESHEET_BASE = r'timesheets/(?P<username>[-\w]+)/(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'

urlpatterns = patterns('officeaid.views',
    (r'^$', 'users.login'),

    # Users
    url(r'^login/$',                                'users.login',           name='login'),
    url(r'^logout/$',                               'users.logout',          name='logout'),
    url(r'^users/$',                                'users.user_list',       name='user_list'),
    url(r'^users/editadmin/$',                      'users.edit_admin_user', name='edit_admin_user'),
    url(r'^users/add/$',                            'users.add_user',        name='add_user'),
    url(r'^users/(?P<username>[-\w]+)/$',           'users.user_detail',     name='user_detail'),
    url(r'^users/(?P<username>[-\w]+)/edit/$',      'users.edit_user',       name='edit_user'),
    url(r'^users/(?P<username>[-\w]+)/rates/$',     'users.edit_user_rates', name='edit_user_rates'),
    url(r'^users/(?P<username>[-\w]+)/rates/add/$', 'users.add_user_rate',   name='add_user_rate'),
    url(r'^users/(?P<username>[-\w]+)/delete/$',    'users.delete_user',     name='delete_user'),

    # Clients
    url(r'^clients/$',                             'clients.client_list',   name='client_list'),
    url(r'^clients/add/$',                         'clients.add_client',    name='add_client'),
    url(r'^clients/(?P<client_id>\d+)/$',          'clients.client_detail', name='client_detail'),
    url(r'^clients/(?P<client_id>\d+)/edit/$',     'clients.edit_client',   name='edit_client'),
    url(r'^clients/(?P<client_id>\d+)/delete/$',   'clients.delete_client', name='delete_client'),

    # Contacts
    url(r'^contacts/$',                                  'contacts.contact_list',    name='contact_list'),
    url(r'^contacts/add/$',                              'contacts.add_contact',     name='add_contact'),
    url(r'^contacts/(?P<contact_id>\d+)/$',              'contacts.contact_detail',  name='contact_detail'),
    url(r'^contacts/(?P<contact_id>\d+)/edit/$',         'contacts.edit_contact',    name='edit_contact'),
    url(r'^contacts/(?P<contact_id>\d+)/delete/$',       'contacts.delete_contact',  name='delete_contact'),
    url(r'^contacts/assign/(?P<mode>single|multiple)/$', 'contacts.assign_contacts', name='assign_contacts'),

    # Task Types
    url(r'^task_types/$',                                 'task_types.task_type_list',       name='task_type_list'),
    url(r'^task_types/add/$',                             'task_types.add_task_type',        name='add_task_type'),
    url(r'^task_types/(?P<task_type_id>\d+)/$',           'task_types.task_type_detail',     name='task_type_detail'),
    url(r'^task_types/(?P<task_type_id>\d+)/edit/$',      'task_types.edit_task_type',       name='edit_task_type'),
    url(r'^task_types/(?P<task_type_id>\d+)/rates/$',     'task_types.edit_task_type_rates', name='edit_task_type_rates'),
    url(r'^task_types/(?P<task_type_id>\d+)/rates/add/$', 'task_types.add_task_type_rate',   name='add_task_type_rate'),
    url(r'^task_types/(?P<task_type_id>\d+)/delete/$',    'task_types.delete_task_type',     name='delete_task_type'),

    # Jobs
    url(r'^jobs/$',                                    'jobs.job_list',           name='job_list'),
    url(r'^jobs/add/$',                                'jobs.add_job',            name='add_job'),
    url(r'^jobs/(?P<job_number>\d+)/$',                'jobs.job_detail',         name='job_detail'),
    url(r'^jobs/(?P<job_number>\d+)/edit/$',           'jobs.edit_job',           name='edit_job'),
    url(r'^jobs/(?P<job_number>\d+)/delete/$',         'jobs.delete_job',         name='delete_job'),
    url(r'^jobs/(?P<job_number>\d+)/previewquote/$',   'jobs.preview_job_quote',  name='preview_job_quote'),
    url(r'^jobs/(?P<job_number>\d+)/generatewquote/$', 'jobs.generate_job_quote', name='generate_job_quote'),

    # Artifacts
    url(r'^jobs/(?P<job_number>\d+)/artifacts/$',                               'artifacts.artifact_list',     name='artifact_list'),
    url(r'^jobs/(?P<job_number>\d+)/artifacts/add/$',                           'artifacts.add_artifact',      name='add_artifact'),
    url(r'^jobs/(?P<job_number>\d+)/artifacts/(?P<artifact_id>\d+)/$',          'artifacts.artifact_detail',   name='artifact_detail'),
    url(r'^jobs/(?P<job_number>\d+)/artifacts/(?P<artifact_id>\d+)/download/$', 'artifacts.download_artifact', name='download_artifact'),
    url(r'^jobs/(?P<job_number>\d+)/artifacts/(?P<artifact_id>\d+)/edit/$',     'artifacts.edit_artifact',     name='edit_artifact'),
    url(r'^jobs/(?P<job_number>\d+)/artifacts/(?P<artifact_id>\d+)/delete/$',   'artifacts.delete_artifact',   name='delete_artifact'),

    # Activities
    url(r'^activities/$',                               'activities.activity_list',   name='activity_list'),
    url(r'^activities/add/$',                           'activities.add_activity',    name='add_activity'),
    url(r'^activities/(?P<activity_id>\d+)/$',          'activities.activity_detail', name='activity_detail'),
    url(r'^activities/(?P<activity_id>\d+)/edit/$',     'activities.edit_activity',   name='edit_activity'),
    url(r'^activities/(?P<activity_id>\d+)/delete/$',   'activities.delete_activity', name='delete_activity'),

    # Expense Types
    url(r'^expense_types/$',                                 'expense_types.expense_type_list',   name='expense_type_list'),
    url(r'^expense_types/add/$',                             'expense_types.add_expense_type',    name='add_expense_type'),
    url(r'^expense_types/(?P<expense_type_id>\d+)/$',        'expense_types.expense_type_detail', name='expense_type_detail'),
    url(r'^expense_types/(?P<expense_type_id>\d+)/edit/$',   'expense_types.edit_expense_type',   name='edit_expense_type'),
    url(r'^expense_types/(?P<expense_type_id>\d+)/delete/$', 'expense_types.delete_expense_type', name='delete_expense_type'),

    # Activity Types
    url(r'^activity_types/$',                                  'activity_types.activity_type_list',   name='activity_type_list'),
    url(r'^activity_types/add/$',                              'activity_types.add_activity_type',    name='add_activity_type'),
    url(r'^activity_types/(?P<activity_type_id>\d+)/$',        'activity_types.activity_type_detail', name='activity_type_detail'),
    url(r'^activity_types/(?P<activity_type_id>\d+)/edit/$',   'activity_types.edit_activity_type',   name='edit_activity_type'),
    url(r'^activity_types/(?P<activity_type_id>\d+)/delete/$', 'activity_types.delete_activity_type', name='delete_activity_type'),

    # Timesheets
    url(r'^timesheets/$',                                                     'timesheets.timesheet_index',       name='timesheet_index'),
    url(r'^timesheets/bulk_approval/$',                                       'timesheets.bulk_approval',         name='bulk_approval'),
    url(r'^%s/$' % TIMESHEET_BASE,                                            'timesheets.edit_timesheet',        name='edit_timesheet'),
    url(r'^%s/approve/' % TIMESHEET_BASE,                                     'timesheets.approve_timesheet',     name='approve_timesheet'),
    url(r'^%s/prepopulate/$' % TIMESHEET_BASE,                                'timesheets.prepopulate_timesheet', name='prepopulate_timesheet'),
    url(r'^%s/time_entries/add/$' % TIMESHEET_BASE,                           'timesheets.add_time_entry',        name='add_time_entry'),
    url(r'^%s/time_entries/(?P<time_entry_id>\d+)/delete/$' % TIMESHEET_BASE, 'timesheets.delete_time_entry',     name='delete_time_entry'),
    url(r'^%s/expenses/add/$' % TIMESHEET_BASE,                               'timesheets.add_expense',           name='add_expense'),
    url(r'^%s/expenses/(?P<expense_id>\d+)/delete/$' % TIMESHEET_BASE,        'timesheets.delete_expense',        name='delete_expense'),

    # Invoices
    url(r'^invoices/$',                                  'invoices.invoice_list',     name='invoice_list'),
    url(r'^invoices/create/$',                           'invoices.invoice_wizard',   name='create_invoices'),
    url(r'^invoices/(?P<invoice_number>\d+)/$',          'invoices.invoice_detail',   name='invoice_detail'),
    url(r'^invoices/(?P<invoice_number>\d+)/edit/$',     'invoices.edit_invoice',     name='edit_invoice'),
    url(r'^invoices/(?P<invoice_number>\d+)/download/$', 'invoices.download_invoice', name='download_invoice'),
    url(r'^invoices/(?P<invoice_number>\d+)/delete/$',   'invoices.delete_invoice',   name='delete_invoice'),

    # Reports
    url(r'^reports/$',                    'reports.report_list',               name='report_list'),
    url(r'^reports/annual_leave/$',       'reports.annual_leave_report',       name='annual_leave_report'),
    url(r'^reports/client/$',             'reports.client_report',             name='client_report'),
    url(r'^reports/developer_progress/$', 'reports.developer_progress_report', name='developer_progress_report'),
    url(r'^reports/invoiced_work/$',      'reports.invoiced_work_report',      name='invoiced_work_report'),
    url(r'^reports/job_expenses/$',       'reports.job_expenses_report',       name='job_expenses_report'),
    url(r'^reports/job_full/$',           'reports.job_full_report',           name='job_full_report'),
    url(r'^reports/job_list/$',           'reports.job_list_report',           name='job_list_report'),
    url(r'^reports/job_list_summary/$',   'reports.job_list_summary_report',   name='job_list_summary_report'),
    url(r'^reports/job_reports/$',        'reports.job_report_list',           name='job_report_list'),
    url(r'^reports/job_status/$',         'reports.job_status_report',         name='job_status_report'),
    url(r'^reports/jobs_missingdata/$',   'reports.jobs_missing_data_report',  name='jobs_missing_data_report'),
    url(r'^reports/jobs_worked_on/$',     'reports.jobs_worked_on_report',     name='jobs_worked_on_report'),
    url(r'^reports/timesheet/$',          'reports.timesheet_report',          name='timesheet_report'),
    url(r'^reports/timesheet_reports/$',  'reports.report_list',               name='timesheet_report_list'),
    url(r'^reports/timesheet_status/$',   'reports.timesheet_status_report',   name='timesheet_status_report'),
    url(r'^reports/uninvoiced_work/$',    'reports.uninvoiced_work_report',    name='uninvoiced_work_report'),
    url(r'^reports/user/$',               'reports.user_report',               name='user_report'),

    # SQL Reports
    url(r'^sql_reports/$',                                'sql_reports.sql_report_list',    name='sql_report_list'),
    url(r'^sql_reports/add/$',                            'sql_reports.add_sql_report',     name='add_sql_report'),
    url(r'^sql_reports/(?P<sql_report_id>\d+)/$',         'sql_reports.sql_report_detail',  name='sql_report_detail'),
    url(r'^sql_reports/(?P<sql_report_id>\d+)/edit/$',    'sql_reports.edit_sql_report',    name='edit_sql_report'),
    url(r'^sql_reports/(?P<sql_report_id>\d+)/delete/$',  'sql_reports.delete_sql_report',  name='delete_sql_report'),
    url(r'^sql_reports/(?P<sql_report_id>\d+)/execute/$', 'sql_reports.execute_sql_report', name='execute_sql_report'),
)

# Admin and settings applications
urlpatterns += patterns('',
    (r'^admin/', include('django_docs.urls')),
    (r'^admin/', include('django.contrib.admin.urls')),
    (r'^settings/', include('dbsettings.urls')),
)
