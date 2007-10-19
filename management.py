from decimal import Decimal

from dbsettings.utils import set_defaults

from officeaid import models as officeaid_app

# Install default OfficeAid settings
set_defaults(officeaid_app,
    ('',          'job_over_hours',                    True),
    ('',          'job_missed_end_date',               True),
    ('',          'incomplete_timesheet',              True),
    ('',          'expense_over_limit',                True),
    ('',          'activity_missed_due_date',          True),
    ('',          'activity_user_assigned',            True),
    ('',          'activity_contact_assigned',         True),
    ('',          'managers_view_all_jobs',            True),
    ('',          'managers_view_all_users',           True),
    ('',          'pc_restricted_to_coordinated_jobs', False),
    ('',          'users_view_all_jobs',               True),
    ('Task',      'vacation_task_id',                  1),
    ('Invoice',   'driven_by',                         'U'),
    ('Invoice',   'uk_vat',                            Decimal('17.5')),
    ('Invoice',   'euro_vat',                          Decimal('21.5')),
    ('Invoice',   'exchange_rate',                     Decimal('1.5')),
    ('Timesheet', 'hours_per_full_week',               Decimal('37.5')),
)
