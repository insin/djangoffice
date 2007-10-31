import datetime
import re
from decimal import Decimal

import dbsettings
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import (RequiredIfOtherFieldEquals,
    RequiredIfOtherFieldGiven, RequiredIfOtherFieldNotGiven)
from django.db import connection, models
from django.db.models.query import find_field
from django.utils.text import truncate_words
from django.utils.encoding import smart_unicode

from officeaid.validators import isSafeishQuery, isWeekCommencingDate

qn = connection.ops.quote_name

sql_param_re = re.compile(r'::([a-zA-Z]+)')
heading_re = re.compile(r'AS \'([\sa-zA-Z]+)\'')

###########
# Options #
###########

class EmailOptions(dbsettings.Group):
    job_over_hours            = dbsettings.BooleanValue(u'Send email when a Job goes over hours')
    job_missed_end_date       = dbsettings.BooleanValue(u'Send email when a Job misses its end date')
    incomplete_timesheet      = dbsettings.BooleanValue(u'Send email when a Timesheet is incomplete at the end of the week')
    expense_over_limit        = dbsettings.BooleanValue(u'Send email when an Expense amount is over limit')
    activity_missed_due_date  = dbsettings.BooleanValue(u'Send email when an Activity misses its due date')
    activity_user_assigned    = dbsettings.BooleanValue(u'Send an email to a User when they are assigned to an Activity')
    activity_contact_assigned = dbsettings.BooleanValue(u'Send an email to a Contact when they are assigned to an Activity')

email = EmailOptions()

class AccessOptions(dbsettings.Group):
    managers_view_all_jobs        = dbsettings.BooleanValue(u'Managers may view all Jobs')
    managers_view_all_users       = dbsettings.BooleanValue(u'Managers may view all Users')
    pm_restricted_to_managed_jobs = dbsettings.BooleanValue(u'PMs only have PM access to Jobs for which they are the Manager')
    users_view_all_jobs           = dbsettings.BooleanValue(u'Users may view all Jobs')

access = AccessOptions()

ACCESS_CHOICES = (
    (u'A', u'Admin'),
    (u'M', u'Manager'),
    (u'P', u'PM'),
    (u'U', u'User'),
)

#################
# User Profiles #
#################

class UserProfile(models.Model):
    """
    A User's profile - defines user details additional to those present
    in ``django.contrib.auth.models.User``.
    """
    USER_ROLE          = u'U'
    PM_ROLE            = u'P'
    MANAGER_ROLE       = u'M'
    ADMINISTRATOR_ROLE = u'A'
    ROLE_CHOICES = (
        (USER_ROLE, u'User'),
        (PM_ROLE, u'PM'),
        (MANAGER_ROLE, u'Manager'),
        (ADMINISTRATOR_ROLE, u'Administrator'),
    )

    user           = models.ForeignKey(User, unique=True)
    role           = models.CharField(max_length=1, choices=ROLE_CHOICES)
    managed_users  = models.ManyToManyField(User, null=True, blank=True, filter_interface=models.HORIZONTAL, related_name='managers')
    phone_number   = models.CharField(max_length=20, blank=True)
    mobile_number  = models.CharField(max_length=20, blank=True)
    login_attempts = models.SmallIntegerField(default=3, help_text=u'The number of unsuccessful login attempts allowed on this account until it is disabled.')
    disabled       = models.BooleanField(default=False, verbose_name=u'Mark as disabled', help_text=u'Users are never physically removed from the database - they are marked as disabled to preserve all data associated with them.')

    def __unicode__(self):
        return self.user.get_full_name() or self.user.username

    class Meta:
        ordering = ['user']

    class Admin:
        list_display = ('user', 'role', 'phone_number', 'mobile_number',
                        'disabled')
        list_filter = ('role', 'disabled')

    def is_admin(self):
        return self.role == self.ADMINISTRATOR_ROLE

    def is_manager(self):
        return self.role == self.MANAGER_ROLE

    def is_pm(self):
        return self.role == self.PM_ROLE

    def is_user(self):
        return self.role == self.USER_ROLE

class UserRateManager(models.Manager):
    def get_latest_effective_from_for_user(self, user):
        """
        Returns the latest "effective from" date held by a rate for the
        given User, or ``None`` if no rates exist.
        """
        try:
            return super(UserRateManager, self).get_query_set() \
                    .filter(user=user) \
                     .order_by('-effective_from')[0].effective_from
        except IndexError:
            return None

class UserRate(models.Model):
    """
    User rates by date.
    """
    user           = models.ForeignKey(User, edit_inline=models.TABULAR, num_extra_on_change=1, related_name='rates')
    effective_from = models.DateField(core=True)
    standard_rate  = models.DecimalField(max_digits=6, decimal_places=2)
    overtime_rate  = models.DecimalField(max_digits=6, decimal_places=2)
    editable       = models.BooleanField(default=True)

    objects = UserRateManager()

    def __unicode__(self):
        return u'Standard: %s, Overtime: %s' % (self.standard_rate,
                                                self.overtime_rate)

    class Meta:
        # Effective From dates must be unique for a given User
        unique_together = (('user', 'effective_from'),)
        ordering = ['-effective_from', 'user']

    class Admin:
        list_display = ('user', 'effective_from', 'standard_rate',
                        'overtime_rate', 'editable')
        list_display_links = ('effective_from',)
        list_filter = ('user',)

class Vacation(models.Model):
    """
    A vacation record defining a User's entitlement for a given year.
    """
    user        = models.ForeignKey(User, related_name='vacations')
    year        = models.PositiveIntegerField()
    entitlement = models.DecimalField(max_digits=5, decimal_places=2)
    carry_over  = models.DecimalField(max_digits=5, decimal_places=2, default='0.00')

    def __unicode__(self):
        return u'%s - %s' % (self.year, self.user.get_full_name())

    class Meta:
        # One vacation record per user per year
        unique_together = (('user', 'year'),)

    class Admin:
        list_display = ('user', 'year', 'entitlement', 'carry_over')

############
# Contacts #
############

class Contact(models.Model):
    """
    An external Contact who may be involved with a number Clients, Jobs
    and Activities.
    """
    first_name    = models.CharField(max_length=30)
    last_name     = models.CharField(max_length=30)
    company_name  = models.CharField(max_length=100)
    position      = models.CharField(max_length=50)
    url           = models.URLField(blank=True, verbose_name=u'URL')
    notes         = models.TextField(blank=True)

    # Contact
    phone_number  = models.CharField(max_length=20)
    mobile_number = models.CharField(max_length=20, blank=True)
    fax_number    = models.CharField(max_length=20, blank=True)
    email         = models.EmailField()

    # Address
    street_line_1 = models.CharField(max_length=100)
    street_line_2 = models.CharField(max_length=100, blank=True)
    town_city     = models.CharField(max_length=100, verbose_name=u'Town/city')
    county        = models.CharField(max_length=100, blank=True)
    postcode      = models.CharField(max_length=10)

    def __unicode__(self):
        return self.full_name

    class Meta:
        ordering = ['first_name', 'last_name']

    class Admin:
        list_display = ('full_name', 'company_name', 'position',
                        'phone_number', 'email')
        fields = (
            (None, {
                'fields': ('first_name', 'last_name', 'company_name',
                           'position', 'url', 'notes')
            }),
            (u'Contact Details', {
                'fields': ('phone_number', 'mobile_number', 'fax_number',
                           'email')
            }),
            (u'Address', {
                'fields': ('street_line_1', 'street_line_2', 'town_city',
                           'county', 'postcode')
            }),
        )

    @property
    def full_name(self):
        return u'%s %s' % (self.first_name, self.last_name)

    @property
    def full_address(self, separator=u',\n'):
        address_fields = ['street_line_1', 'street_line_2', 'town_city',
                          'county', 'postcode']
        return separator.join([getattr(self, field) \
                               for field in address_fields \
                               if getattr(self, field)])

    def is_deleteable(self):
        """
        Returns ``True`` if this Contact is deleteable, ``False``
        otherwise.

        A Contact is deleteable if it is not assigned to a Client or to
        a Job in any capacity and does not have any Activities assigned
        to it.
        """
        return self.billing_contact_jobs.count() == 0 and \
               self.primary_contact_jobs.count() == 0 and \
               self.job_contact_jobs.count() == 0 and \
               self.clients.count() == 0 and \
               self.activities.count() == 0

    @models.permalink
    def get_absolute_url(self):
        return ('contact_detail', (smart_unicode(self.id),))

class Client(models.Model):
    """
    A Client for whom Jobs may be worked on.
    """
    name     = models.CharField(max_length=100)
    notes    = models.TextField(blank=True)
    contacts = models.ManyToManyField(Contact, filter_interface=models.HORIZONTAL, related_name='clients')
    disabled = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def is_deleteable(self):
        """
        Returns ``True`` if this Client is deleteable, ``False``
        otherwise.

        A Client is deleteable if it does not have any Jobs.
        """
        return self.jobs.count() == 0

    class Meta:
        ordering = ['name']

    class Admin:
        list_display = ('name', 'notes', 'disabled')

    @models.permalink
    def get_absolute_url(self):
        return ('client_detail', (smart_unicode(self.id),))

########
# Jobs #
########

class TaskTypeManager(models.Manager):
    def non_admin(self):
        """
        Creates a ``QuerySet`` containing Task Types which are not
        associated with Admin Job Tasks.
        """
        opts = self.model._meta
        task_opts = Task._meta
        return super(TaskTypeManager, self).get_query_set().extra(
            where=['%s.%s NOT IN (SELECT %s FROM %s WHERE %s = %%s)' % (
               qn(opts.db_table), qn(opts.pk.column),
               qn(task_opts.get_field('task_type').column),
               qn(task_opts.db_table), qn(task_opts.get_field('job').column)
            )],
            params=[settings.ADMIN_JOB_ID],
        )

    def exclude_by_job(self, job_id):
        """
        Creates a ``QuerySet`` containing Task Types which are not
        associated with Admin Job Tasks or Tasks for the Job with the
        given id.
        """
        opts = self.model._meta
        task_opts = Task._meta
        return super(TaskTypeManager, self).get_query_set().extra(
            where=['%s.%s NOT IN (SELECT %s FROM %s WHERE %s IN (%%s, %%s))' % (
               qn(opts.db_table), qn(opts.pk.column),
               qn(task_opts.get_field('task_type').column),
               qn(task_opts.db_table), qn(task_opts.get_field('job').column)
            )],
            params=[settings.ADMIN_JOB_ID, job_id],
        )

class TaskType(models.Model):
    """
    A type of work which may be carried out as part of a Job.
    """
    name    = models.CharField(max_length=100, unique=True)

    objects = TaskTypeManager()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

    class Admin:
        list_display = ('name',)

    def is_deleteable(self):
        """
        Returns ``True`` if this Task Type is deleteable, ``False``
        otherwise.

        A Task Type is deleteable if there are no Tasks created with it
        set as their type.
        """
        return self.tasks.count() == 0

    @models.permalink
    def get_absolute_url(self):
        return ('task_type_detail', (smart_unicode(self.id),))

class TaskTypeRateManager(models.Manager):
    def get_latest_effective_from_for_task_type(self, task_type):
        """
        Returns the latest "effective from" date held by a rate for the
        given Task Type, or ``None`` if no rates exist.
        """
        try:
            return super(TaskTypeRateManager, self).get_query_set() \
                    .filter(task_type=task_type) \
                     .order_by('-effective_from')[0].effective_from
        except IndexError:
            return None

class TaskTypeRate(models.Model):
    """
    Rates by date for a given type of work.
    """
    task_type      = models.ForeignKey(TaskType, edit_inline=models.TABULAR, related_name='rates')
    effective_from = models.DateField(core=True)
    standard_rate  = models.DecimalField(max_digits=6, decimal_places=2)
    overtime_rate  = models.DecimalField(max_digits=6, decimal_places=2)
    editable       = models.BooleanField(default=True)

    objects = TaskTypeRateManager()

    def __unicode__(self):
        return u'Standard: %s, Overtime: %s' % (self.standard_rate, self.overtime_rate)

    class Meta:
        # Effective from dates must be unique for a given TaskType
        unique_together = (('task_type', 'effective_from'),)
        ordering = ['-effective_from', 'task_type']
        verbose_name = 'Task type rate'

    class Admin:
       list_display = ('task_type', 'effective_from', 'standard_rate',
                       'overtime_rate', 'editable')
       list_display_links = ('effective_from',)
       list_filter = ('task_type',)

class JobManager(models.Manager):
    def get_next_free_number(self):
        """
        Determines the next free Job number.
        """
        opts = self.model._meta
        query = """
        SELECT j1.%(number)s + 1
        FROM %(job)s AS j1
        LEFT JOIN %(job)s AS j2
            ON j2.%(number)s = j1.%(number)s + 1
        WHERE j2.%(number)s IS NULL
        ORDER BY j1.%(number)s %(limit)s""" % {
            'job': qn(opts.db_table),
            'number': qn(opts.get_field('number').column),
            'limit': connection.ops.limit_offset_sql(1),
        }
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        try:
            return result[0][0]
        except IndexError:
            return 1

    def accessible_to_user(self, user):
        """
        Creates a ``QuerySet`` containing Jobs the given User may access
        based on their role.

        Admins may always see all Jobs, as may other roles when the
        appropriate access setting is enabled.

        Otherwise, Users may only see Jobs for which they are assigned
        to work on a Task.

        Note that the Administration Job should never be visible; this
        Job exists purely to track vacations and other "internal"
        time.
        """
        profile = user.get_profile()
        qs = super(JobManager, self)\
              .get_query_set() \
               .exclude(pk=settings.ADMIN_JOB_ID)
        if profile.is_admin() or \
           profile.is_manager() and access.managers_view_all_jobs or \
           profile.is_pm() and access.users_view_all_jobs or \
           profile.is_user() and access.users_view_all_jobs:
            pass
        else:
            opts = self.model._meta
            task_opts = Task._meta
            assigned_users_rel = find_field('assigned_users',
                                            task_opts.many_to_many, False)
            qs = qs.extra(
                where=["""
                %(job)s.%(job_pk)s IN (
                    SELECT DISTINCT %(task)s.%(job_fk)s
                    FROM %(task)s
                    INNER JOIN %(assigned_users)s
                        ON %(assigned_users)s.%(task_fk)s = %(task)s.%(task_pk)s
                    WHERE %(assigned_users)s.%(user_fk)s = %%s
                )""" % {
                    'job': qn(opts.db_table),
                    'job_pk': qn(opts.pk.column),
                    'job_fk': qn(task_opts.get_field('job').column),
                    'task': qn(task_opts.db_table),
                    'task_pk': qn(task_opts.pk.column),
                    'task_fk': qn(assigned_users_rel.m2m_column_name()),
                    'assigned_users': qn(assigned_users_rel.m2m_db_table()),
                    'user_fk': qn(assigned_users_rel.m2m_reverse_name()),
                }],
                params=[user.id],
            )

            if profile.is_manager():
                qs = qs | super(JobManager, self).get_query_set() \
                                                  .filter(director_id=user.pk)
            elif profile.is_pm():
                qs = qs | super(JobManager, self).get_query_set() \
                                                  .filter(project_manager_id=user.pk)
        return qs

class Job(models.Model):
    """
    A Job worked on for a Client.

    Each Job has a number of Tasks which define the work to be carried
    out for it.
    """
    QUOTE_STATUS     = u'Q'
    LIVE_STATUS      = u'L'
    SUSPENDED_STATUS = u'S'
    COMPLETED_STATUS = u'C'
    ARCHIVED_STATUS  = u'A'
    STATUS_CHOICES = (
        (QUOTE_STATUS, u'Quote'),
        (LIVE_STATUS, u'Live'),
        (SUSPENDED_STATUS, u'Suspended'),
        (COMPLETED_STATUS, u'Completed'),
        (ARCHIVED_STATUS, u'Archived'),
    )

    SET_FEE          = u'S'
    TIME_CHARGED_FEE = u'T'
    PERCENTAGE_FEE   = u'P'
    FEE_BASIS_CHOICES = (
        (SET_FEE, u'Set Fee'),
        (TIME_CHARGED_FEE, u'Time Charged'),
        (PERCENTAGE_FEE, u'Percentage'),
    )

    GBP_CURRENCY  = u'GBP'
    EURO_CURRENCY = u'EUR'
    FEE_CURRENCY_CHOICES = (
        (GBP_CURRENCY, u'GBP'),
        (EURO_CURRENCY, u'Euro'),
    )

    client             = models.ForeignKey(Client, related_name='jobs')
    name               = models.CharField(max_length=100)
    number             = models.PositiveIntegerField(unique=True)
    reference          = models.CharField(max_length=16, blank=True)
    reference_date     = models.DateField(null=True, blank=True)
    add_reference      = models.CharField(max_length=16, blank=True)
    add_reference_date = models.DateField(null=True, blank=True)
    status             = models.CharField(max_length=1, choices=STATUS_CHOICES)
    notes              = models.TextField(blank=True)
    invoice_notes      = models.TextField(blank=True)
    contingency        = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Users
    director            = models.ForeignKey(User, related_name='directed_jobs')
    project_coordinator = models.ForeignKey(User, null=True, blank=True, related_name='coordinated_jobs')
    project_manager     = models.ForeignKey(User, related_name='managed_jobs')
    architect           = models.ForeignKey(User, related_name='architected_jobs')

    # Contacts
    primary_contact = models.ForeignKey(Contact, related_name='primary_contact_jobs')
    billing_contact = models.ForeignKey(Contact, related_name='billing_contact_jobs')
    job_contacts    = models.ManyToManyField(Contact, null=True, blank=True, filter_interface=models.HORIZONTAL, related_name='job_contact_jobs')

    # Dates
    created_at = models.DateTimeField(editable=False)
    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True, verbose_name='Expected end date')

    # Fee
    fee_basis    = models.CharField(max_length=1, blank=True, choices=FEE_BASIS_CHOICES)
    fee_amount   = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validator_list=[RequiredIfOtherFieldEquals('fee_basis', 'S', u'This field is required if Fee Basis is Set Fee.'), RequiredIfOtherFieldEquals('fee_basis', 'P', u'This field is required if Fee Basis is Percentage.')])
    fee_currency = models.CharField(max_length=3, choices=FEE_CURRENCY_CHOICES)

    # Notification
    missed_end_date = models.BooleanField(default=False, verbose_name=u'Notified about missed end date')
    over_hours      = models.BooleanField(default=False, verbose_name=u'Notified about going over hours')

    objects = JobManager()

    def __unicode__(self):
        return u'%s - %s' % (self.formatted_number, self.name)

    class Meta:
        ordering = ['-created_at']

    class Admin:
        list_display = ('name', 'number', 'status', 'client')
        list_filter = ('status', 'client')
        fields = (
            (None, {
                'fields': ('client', 'name', 'number', 'reference',
                           'reference_date', 'add_reference',
                           'add_reference_date', 'status', 'notes',
                           'invoice_notes', 'contingency')
            }),
            (u'Users', {
                'fields': ('director', 'project_coordinator',
                           'project_manager', 'architect')
            }),
            (u'Contacts', {
                'fields': ('primary_contact', 'billing_contact',
                           'job_contacts')
            }),
            (u'Dates', {
                'fields': ('start_date', 'end_date')
            }),
            (u'Fee', {
                'fields': ('fee_currency', 'fee_basis', 'fee_amount')
            }),
            (u'Notification', {
                'fields': ('missed_end_date', 'over_hours')
            }),
        )

    def save(self):
        if not self.id:
            self.created_at = datetime.datetime.now()
        if not self.number:
            self.number = self._default_manager.get_next_free_number()
        super(Job, self).save()

    @property
    def formatted_number(self):
        return u'%05d' % (self.number,)

    def is_accessible_to_user(self, user):
        """
        Returns ``True`` if this Job may be accessed by the given User,
        ``False`` otherwise.
        """
        return self._default_manager \
                    .accessible_to_user(user) \
                     .filter(pk=self.id) \
                      .count() > 0

    def is_deleteable(self):
        """
        Returns ``True`` if this Job is deleteable, ``False`` otherwise.

        A Job is deleteable if there are no Expenses booked against it
        and no Timesheets booked against its Tasks.

        The Administration Job is never deleteable.

        The check for ``NULL`` when counting Tasks which have Time
        Entries booked against them is redundant - this check works on
        the principle that the ORM will ``INNER JOIN`` the Time Entry
        table on the Task table, thus eliminating Tasks without any Time
        Entries booked against them from the result set.
        """
        return self.id != settings.ADMIN_JOB_ID and \
               self.expenses.count() == 0 and \
               self.tasks.filter(time_entries__id__isnull=False).count() == 0

    @models.permalink
    def get_absolute_url(self):
        return ('job_detail', (self.formatted_number,))

class TaskOptions(dbsettings.Group):
    vacation_task_id = dbsettings.PositiveIntegerValue(u'Vacation Task id')

class TaskManager(models.Manager):
    def with_task_type_name(self):
        """
        Creates a ``QuerySet`` containing Tasks, giving each Task an additional
        ``task_type_name`` attribute containing the name of its Task, Type.
        """
        opts = self.model._meta
        task_type_opts = TaskType._meta
        task_type_table = qn(task_type_opts.db_table)
        return super(TaskManager, self).get_query_set().extra(
            select={
                'task_type_name': '%s.%s' % (
                    task_type_table,
                    qn(task_type_opts.get_field('name').column),
                 ),
            },
            tables=[task_type_table],
            where=['%s.%s = %s.%s' % (
                qn(opts.db_table),
                qn(opts.get_field('task_type').column),
                task_type_table,
                qn(task_type_opts.pk.column),
            )]
        ).order_by('task_type_name')

    def for_user_timesheet(self, user):
        """
        Creates a ``QuerySet`` containing all Tasks to which the given
        User is assigned, giving each Task an additional
        ``task_type_name`` attribute containing the name of its Task
        Type.
        """
        return self.with_task_type_name().filter(assigned_users=user)

class Task(models.Model):
    """
    A single piece of work which constitutes part of a Job.

    Each Task may have a number of Users assigned to work on it.
    """
    job                  = models.ForeignKey(Job, related_name='tasks', edit_inline=models.TABULAR)
    task_type            = models.ForeignKey(TaskType, related_name='tasks', core=True)
    estimate_hours       = models.DecimalField(max_digits=6, decimal_places=2)
    assigned_users       = models.ManyToManyField(User, filter_interface=models.HORIZONTAL, related_name='tasks', help_text=u'These users will be able to book time against this task.')
    start_date           = models.DateField(null=True, blank=True)
    end_date             = models.DateField(null=True, blank=True)
    remaining            = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remaining_overridden = models.BooleanField(help_text=u'This field indicates whether or not the Task\'s remaining field has been overridden by a user.')

    options = TaskOptions()
    objects = TaskManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.task_type.name, self.job.name)

    class Meta:
        # Only one Task may have a given Task Type per Job
        unique_together = (('job', 'task_type'),)

    class Admin:
        list_display = ('job', 'task_type', 'estimate_hours', 'start_date',
                        'end_date', 'remaining', 'remaining_overridden')
        list_display_links = ('task_type',)

    @property
    def total_time_booked(self):
        hours = [t.get_total_time_booked() for t in self.timesheets.all()]
        return sum(hours)

    @property
    def estimate_cost(self):
        # TODO Implement
        pass

class ArtifactType(models.Model):
    """
    A type of artifact.
    """
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

    class Admin:
        list_display = ('name', 'description')

    @property
    def is_deleteable(self):
        """
        An ArtifactType is deleteable if there are no Artifacts created
        with it set as their type.
        """
        return self.artifacts.count() == 0

    @models.permalink
    def get_absolute_url(self):
        return ('artifact_type_detail', (smart_unicode(self.id),))

class ArtifactManager(models.Manager):
    def accessible_to_user(self, user):
        """
        Creates a ``QuerySet`` containing Artifacts accessible by the
        given User based on their role.
        """
        user_profile = user.get_profile()
        qs = super(ArtifactManager, self).get_query_set()
        if user_profile.is_manager():
            qs = qs.filter(access__in=[UserProfile.MANAGER_ROLE, UserProfile.PM_ROLE, UserProfile.USER_ROLE])
        elif user_profile.is_pm():
            qs = qs.filter(access__in=[UserProfile.PM_ROLE, UserProfile.USER_ROLE])
        elif user_profile.is_user():
            qs = qs.filter(access=UserProfile.USER_ROLE)
        return qs

class Artifact(models.Model):
    """
    A file related to a particular Job, access to which may be
    restricted based on a User's role.
    """
    job         = models.ForeignKey(Job, related_name='artifacts')
    file        = models.FileField(upload_to='artifacts')
    type        = models.ForeignKey(ArtifactType, null=True, blank=True, related_name='artifacts')
    description = models.CharField(max_length=100)
    created_at  = models.DateTimeField(editable=False)
    updated_at  = models.DateTimeField(editable=False)
    access      = models.CharField(max_length=1, choices=ACCESS_CHOICES)

    objects = ArtifactManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.description, self.job.name)

    class Meta:
        ordering = ['-created_at']

    class Admin:
        list_display = ('file', 'job', 'type', 'description', 'created_at', 'access')
        list_filter = ('created_at', 'access')

    def save(self):
        now = datetime.datetime.now()
        if not self.id:
            self.created_at = now
        self.updated_at = now
        super(Artifact, self).save()

    def is_accessible_to_user(self, user):
        """
        Returns ``True`` if this Artifact may be accessed by the given
        User, ``False`` otherwise.
        """
        return self._default_manager \
                    .accessible_to_user(user) \
                     .filter(pk=self.id) \
                      .count() > 0

class ActivityType(models.Model):
    """
    A type of activity, which confers an access restriction based on user
    role.
    """
    name        = models.CharField(max_length=100, unique=True)
    access      = models.CharField(max_length=1, choices=ACCESS_CHOICES)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

    class Admin:
        list_display = ('name', 'access', 'description')

    @property
    def is_deleteable(self):
        """
        An ActivityType is deleteable if there are no Activities with it
        set as their type.
        """
        return self.activities.count() == 0

    @models.permalink
    def get_absolute_url(self):
        return ('activity_type_detail', (smart_unicode(self.pk),))

class Activity(models.Model):
    """
    A TODO item or a record of some form of interaction with a User or a
    Contact related to a specific Job.
    """
    LOW_PRIORITY    = u'L'
    MEDIUM_PRIORITY = u'M'
    HIGH_PRIORITY   = u'H'
    TOP_PRIORITY    = u'T'
    PRIORITY_CHOICES = (
        (LOW_PRIORITY, u'Low'),
        (MEDIUM_PRIORITY, u'Medium'),
        (HIGH_PRIORITY, u'High'),
        (TOP_PRIORITY, u'Top'),
    )

    job         = models.ForeignKey(Job, related_name='activities')
    type        = models.ForeignKey(ActivityType, null=True, blank=True, related_name='activities')
    created_by  = models.ForeignKey(User, related_name='created_activities')
    created_at  = models.DateTimeField(editable=False)
    description = models.TextField()
    priority    = models.CharField(max_length=1, choices=PRIORITY_CHOICES)
    assigned_to = models.ForeignKey(User, null=True, blank=True, related_name='assigned_activities', verbose_name='User', validator_list=[RequiredIfOtherFieldNotGiven('contact')])
    contact     = models.ForeignKey(Contact, null=True, blank=True, related_name='activities', validator_list=[RequiredIfOtherFieldNotGiven('assigned_to')])
    due_date    = models.DateField(null=True, blank=True)

    # Completion
    completed    = models.BooleanField()
    completed_at = models.DateTimeField(null=True, blank=True, editable=False)

    def __unicode__(self):
        return u'%s - %s' % (self.job, truncate_words(self.description, 50))

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = u'Activities'

    class Admin:
        list_display = ('formatted_number', 'created_by', 'job', 'type',
                        'description', 'assigned_to', 'contact', 'due_date',
                        'priority', 'completed')
        list_filter = ('due_date', 'priority', 'completed')
        fields = (
            (None, {
                'fields': ('job', 'type', 'created_by', 'description',
                           'priority', 'due_date')
            }),
            (u'Assignment', {
                'description': 'An activity may be assigned to a User or a Contact - if both are given, User takes precedence.',
                'fields': ('assigned_to', 'contact'),
            }),
            (u'Completion', {
                'fields': ('completed',)
            }),
        )

    def save(self):
        if not self.id:
            self.created_at = datetime.datetime.now()
        if self.completed and not self.completed_at:
            self.completed_at = datetime.datetime.now()
        # Users take precedence for assignment
        if self.assigned_to and self.contact:
            self.contact = None
        self.description = self.description.strip()
        super(Activity, self).save()

    @property
    def formatted_number(self):
        return u'%05d' % (self.id,)

    @models.permalink
    def get_absolute_url(self):
        return ('activity_detail', (smart_unicode(self.id),))

############
# Invoices #
############

INVOICING_DRIVEN_BY_CHOICES = (
    (u'U', u'User'),
    (u'T', u'Task'),
)

class InvoiceOptions(dbsettings.Group):
    driven_by     = dbsettings.StringValue(choices=INVOICING_DRIVEN_BY_CHOICES)
    uk_vat        = dbsettings.PercentValue(u'UK VAT')
    euro_vat      = dbsettings.PercentValue(u'Euro VAT')
    exchange_rate = dbsettings.DecimalValue(u'GBP to Euro exchange rate')

class InvoiceManager(models.Manager):
    def with_job_details(self):
        """
        Creates a ``QuerySet`` containing Invoices which have
        additional information about the Job which they represent an
        invoice for.
        """
        opts = self.model._meta
        job_opts = Job._meta
        client_opts = Client._meta
        contact_opts = Contact._meta
        job_table = qn(job_opts.db_table)
        client_table = qn(client_opts.db_table)
        contact_table = qn(contact_opts.db_table)
        return super(InvoiceManager, self).get_query_set().extra(
            select={
                'job_number': '%s.%s' % (job_table, qn(job_opts.get_field('number').column)),
                'job_name': '%s.%s' % (job_table, qn(job_opts.get_field('name').column)),
                'job_fee_currency': '%s.%s' % (job_table, qn(job_opts.get_field('fee_currency').column)),
                'client_name': '%s.%s' % (client_table, qn(client_opts.get_field('name').column)),
                'primary_contact_first_name': '%s.%s' % (contact_table, qn(contact_opts.get_field('first_name').column)),
                'primary_contact_last_name': '%s.%s' % (contact_table, qn(contact_opts.get_field('last_name').column)),
            },
            tables=[job_table, client_table, contact_table],
            where=[
                '%s.%s = %s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('job').column),
                    job_table,
                    qn(job_opts.pk.column),
                ),
                '%s.%s = %s.%s' % (
                    job_table,
                    qn(job_opts.get_field('client').column),
                    client_table,
                    qn(client_opts.pk.column),
                ),
                '%s.%s = %s.%s' % (
                    job_table,
                    qn(job_opts.get_field('primary_contact').column),
                    contact_table,
                    qn(contact_opts.pk.column),
                ),
            ]
        )

    def get_next_free_number(self):
        """
        Determines the next free Invoice number.
        """
        opts = self.model._meta
        query = """
        SELECT i1.%(number)s + 1
        FROM %(invoice)s AS i1
        LEFT JOIN %(invoice)s AS i2
            ON i2.%(number)s = i1.%(number)s + 1
        WHERE i2.%(number)s IS NULL
        ORDER BY i1.%(number)s %(limit)s""" % {
            'invoice': qn(opts.db_table),
            'number': qn(opts.get_field('number').column),
            'limit': connection.ops.limit_offset_sql(1),
        }
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        try:
            return result[0][0]
        except IndexError:
            return 1

INVOICE_PERIOD_VALIDATOR = RequiredIfOtherFieldEquals('type', 'D', u'Required for Date Restricted invoices.')

class Invoice(models.Model):
    """
    An invoice for Time Entries and Expenses booked against a Job.
    """
    DATE_RESTRICTED_TYPE = u'D'
    WHOLE_JOB_TYPE       = u'W'
    TYPE_CHOICES = (
        (DATE_RESTRICTED_TYPE, u'Date Restricted'),
        (WHOLE_JOB_TYPE, u'Whole Job'),
    )

    job             = models.ForeignKey(Job,related_name='invoices')
    number          = models.PositiveIntegerField(unique=True)
    date            = models.DateField(editable=False)
    type            = models.CharField(max_length=1, choices=TYPE_CHOICES)
    start_period    = models.DateField(null=True, blank=True, validator_list=[INVOICE_PERIOD_VALIDATOR])
    end_period      = models.DateField(null=True, blank=True, validator_list=[INVOICE_PERIOD_VALIDATOR])
    amount_invoiced = models.DecimalField(max_digits=8, decimal_places=2)
    amount_received = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    adjustment      = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    comment         = models.TextField(blank=True)
    pdf             = models.FileField(upload_to='invoices', blank=True)

    options = InvoiceOptions()
    objects = InvoiceManager()

    def __unicode__(self):
        return u'Invoice #%s' % smart_unicode(self.number)

    class Meta:
       verbose_name = 'Invoice'

    class Admin:
        list_display = ('formatted_number', 'job', 'date', 'type',
                        'start_period', 'end_period','amount_invoiced',
                        'amount_received', 'adjustment', 'comment')
        fields = (
            (None, {
                'fields': ('job', 'number', 'type', 'start_period',
                           'end_period', 'amount_invoiced', 'amount_received',
                           'adjustment', 'comment', 'pdf')
            }),
        )

    def save(self):
        if not self.id:
            self.date = datetime.date.today()
        super(Invoice, self).save()

    @property
    def formatted_number(self):
        return u'%05d' % (self.number,)

    @models.permalink
    def get_absolute_url(self):
        return ('invoice_detail', (self.formatted_number,))

##############
# Timesheets #
##############

class TimesheetOptions(dbsettings.Group):
    hours_per_full_week = dbsettings.DecimalValue()

class TimesheetManager(models.Model):
    def bulk_approve(user, start_date, end_date):
        """
        Marks all unapproved Timesheet items between the given dates as
        approved by the given User, returning a two-tuple indicating how
        many Time Entries and Expenses respectively were marked as
        approved.
        """
        approved_time_entries = TimeEntry.objects.bulk_approve(user, start_date, end_date)
        approved_expenses = Expense.objects.bulk_approve(user, start_date, end_date)
        return (approved_time_entries, approved_expenses)

class Timesheet(models.Model):
    """
    A record of a User's time entries and expenses for a given week.
    """
    user            = models.ForeignKey(User, related_name='timesheets')
    week_commencing = models.DateField(validator_list=[isWeekCommencingDate])

    options = TimesheetOptions()
    objects = TimesheetManager()

    def __unicode__(self):
        return u'%s - %s' % (self.user.get_full_name(), self.week_commencing)

    class Meta:
        # Each user may only have one timesheet per week
        unique_together = (('user', 'week_commencing'),)

    class Admin:
        list_display = ('user', 'week_commencing')

    def url_parts(self, user=None):
        """
        Returns a list of URL parts for this Timesheet to be used for
        reverse URL lookups.

        If a User is given, it will be used to retrieve the username for
        the URL, saving the database query which might be required to
        retrieve this Timesheet's User, if not already fetched.
        """
        return [user is not None and user.username or self.user.username] + \
               self.week_commencing.strftime('%Y/%m/%d').split('/')

    @models.permalink
    def get_absolute_url(self, user=None):
        return ('edit_timesheet', tuple(self.url_parts(user)))

    def approve(self, user):
        """
        Marks all unapproved items on this Timesheet as approved by the
        given User, returning a two-tuple indicating how many Time
        Entries and Expenses respectively were marked as approved.
        """
        cursor = connection.cursor()

        time_entry_opts = TimeEntry._meta
        query = """
        UPDATE %(time_entry)s
        SET %(approved_by)s = %%s
        WHERE %(approved_by)s IS NULL
          AND %(timesheet_fk)s = %%s""" % {
            'time_entry': qn(time_entry_opts.db_table),
            'approved_by': qn(time_entry_opts.get_field('approved_by').column),
            'timesheet_fk': qn(time_entry_opts.get_field('timesheet').column),
        }
        cursor.execute(query, [user.id, self.id])
        approved_time_entries = cursor.rowcount

        expense_opts = Expense._meta
        query = """
        UPDATE %(expense)s
        SET %(approved_by)s = %%s
        WHERE %(approved_by)s IS NULL
          AND %(timesheet_fk)s = %%s""" % {
            'expense': qn(expense_opts.db_table),
            'approved_by': qn(expense_opts.get_field('approved_by').column),
            'timesheet_fk': qn(expense_opts.get_field('timesheet').column),
        }
        cursor.execute(query, [user.id, self.id])
        approved_expenses = cursor.rowcount

        return (approved_time_entries, approved_expenses)

class TimeEntryManager(models.Manager):
    def for_timesheet(self, timesheet):
        """
        Creates a ``QuerySet`` containing all Time Entries associated
        with the given Timesheet, giving each Time Entry additional Task
        and Job details as required for display when editing a complete
        Timesheet.
        """
        opts = self.model._meta
        task_opts = Task._meta
        task_type_opts = TaskType._meta
        job_opts = Job._meta
        task_table = qn(task_opts.db_table)
        task_type_table = qn(task_type_opts.db_table)
        job_table = qn(job_opts.db_table)
        return super(TimeEntryManager, self).get_query_set().filter(timesheet=timesheet).extra(
            select={
                'job_id': '%s.%s' % (task_table, qn(task_opts.get_field('job').column)),
                'job_number': '%s.%s' % (job_table, qn(job_opts.get_field('number').column)),
                'job_name': '%s.%s' % (job_table, qn(job_opts.get_field('name').column)),
                'task_name': '%s.%s' % (task_type_table, qn(task_type_opts.get_field('name').column)),
                'task_estimate_hours': '%s.%s' % (task_table, qn(task_opts.get_field('estimate_hours').column)),
                'task_remaining': '%s.%s' % (task_table, qn(task_opts.get_field('remaining').column)),
            },
            tables=[task_table, task_type_table, job_table],
            where=[
                '%s.%s = %s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('task').column),
                    task_table,
                    qn(task_opts.pk.column),
                ),
                '%s.%s = %s.%s' % (
                    qn(task_table),
                    qn(task_opts.get_field('task_type').column),
                    task_type_table,
                    qn(task_type_opts.pk.column),
                ),
                '%s.%s = %s.%s' % (
                    qn(task_table),
                    qn(task_opts.get_field('job').column),
                    job_table,
                    qn(job_opts.pk.column),
                ),
            ]
        )

    def hours_booked_for_tasks(self, task_ids):
        """
        Creates a dictionary mapping Task ids to the total number of
        hours booked by all Users against Tasks with the given ids.
        """
        if len(task_ids) == 0:
            return {}

        opts = self.model._meta
        task_opts = Task._meta
        time_entry_table = qn(opts.db_table)
        query = """
        SELECT %(task)s.%(task_pk)s, SUM(%(time_columns)s) AS %(booked)s
        FROM %(time_entry)s
        INNER JOIN %(task)s ON %(task)s.%(task_pk)s = %(time_entry)s.%(task_fk)s
        WHERE %(task)s.%(task_pk)s IN (%(task_pks)s)
        GROUP BY %(task)s.%(task_pk)s""" % {
            'task': qn(task_opts.db_table),
            'task_pk': qn(task_opts.pk.column),
            'time_columns': '+'.join(['%s.%s' \
                                      % (time_entry_table,
                                         qn(opts.get_field(attr).column)) \
                                      for attr in TimeEntry.TIME_ATTRS]),
            'booked': qn('booked'),
            'time_entry': time_entry_table,
            'task_fk': qn(opts.get_field('task').column),
            'task_pks': ','.join(['%s'] * len(task_ids)),
        }
        cursor = connection.cursor()
        cursor.execute(query, task_ids)
        results = cursor.fetchall()
        return dict([(task_id, Decimal(str(booked))) \
                     for task_id, booked in results])

    def for_job(job):
        """
        Creates a ``QuerySet`` containing all Time Entries booked
        against Tasks for the given Job.
        """
        return super(TimeEntryManager, self) \
                .get_query_set() \
                 .filter(task__job=job) \
                  .select_related()

    def bulk_approve(self, user, start_date, end_date):
        """
        Marks all unapproved Time Entries on Timesheets with
        ``week_commencing`` dates between the given dates as approved by
        the given User and returns the number of rows updated.
        """
        opts = self.model._meta
        timesheet_opts = Timesheet._meta
        query = """
        UPDATE %(time_entry)s
        SET %(approved_by)s = %%s
        WHERE %(approved_by)s IS NULL
          AND %(timesheet_fk)s IN (
              SELECT %(timesheet_pk)s
              FROM %(timesheet)s
              WHERE %(week_commencing)s >= %%s AND %(week_commencing)s <= %%s
          )""" % {
            'time_entry': qn(opts.db_table),
            'approved_by': qn(opts.get_field('approved_by').column),
            'timesheet_fk': qn(opts.get_field('timesheet').column),
            'timesheet_pk': qn(timesheet_opts.pk.column),
            'timesheet': qn(timesheet_opts.db_table),
            'week_commencing': qn(timesheet_opts.get_field('week_commencing').column),
        }
        cursor = connection.cursor()
        cursor.execute(query, [user.id, start_date, end_date])
        return cursor.rowcount

class TimeEntry(models.Model):
    """
    Time booked against a Job Task.
    """
    TIME_ATTRS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'overtime')

    timesheet       = models.ForeignKey(Timesheet, related_name='time_entries', edit_inline=models.TABULAR)
    user            = models.ForeignKey(User, related_name='time_entries')
    task            = models.ForeignKey(Task, related_name='time_entries', core=True)
    week_commencing = models.DateField(validator_list=[isWeekCommencingDate])
    mon             = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    tue             = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    wed             = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    thu             = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    fri             = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    sat             = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    sun             = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    overtime        = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    description     = models.CharField(max_length=100, blank=True)
    billable        = models.BooleanField(default=True)

    # Administration
    approved_by = models.ForeignKey(User, null=True, blank=True, related_name='approved_time_entries')
    invoice     = models.ForeignKey(Invoice, null=True, blank=True, related_name='time_entries')

    objects = TimeEntryManager()

    def __unicode__(self):
        return u'%s - %s - %s' % (self.timesheet.user.get_full_name(),
                                  self.timesheet.week_commencing.isoformat(),
                                  self.task.task_type.name)

    class Meta:
        verbose_name_plural = u'Time entries'

    class Admin:
        list_display = ('user', 'task', 'week_commencing', 'total_time_booked',
                        'overtime', 'description', 'billable')
        fields = (
            (None, {
                'fields': ('timesheet', 'user', 'task', 'week_commencing',
                           'task', ('mon', 'tue', 'wed', 'thu', 'fri', 'sat',
                           'sun'), 'overtime', 'description', 'billable')
            }),
            (u'Administration', {
                'fields': ('approved_by', 'invoice'),
            }),
        )

    def save(self):
        """
        Ensure time fields are not ``None`` before a save is performed.
        """
        for attr in self.TIME_ATTRS:
            if getattr(self, attr) is None:
                setattr(self, attr, 0.0)
        super(TimeEntry, self).save()

    @property
    def total_time_booked(self):
        return self.mon + self.tue + self.wed + self.thu + self.fri + \
               self.sat + self.sun

    def is_editable(self):
        return self.invoice_id is None and self.approved_by_id is None

    def is_approved(self):
        return self.invoice_id is None and self.approved_by_id is not None

    def is_invoiced(self):
        return self.invoice_id is not None

    def is_deleteable(self):
        return self.is_editable()

############
# Expenses #
############

class ExpenseType(models.Model):
    """
    A type of expense.
    """
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    limit       = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

    class Admin:
        list_display = ('name', 'description', 'limit')

    @property
    def is_deleteable(self):
        """
        An ExpenseType is deleteable if there are no expenses created
        with it set as their type.
        """
        return self.expenses.count() == 0

    @models.permalink
    def get_absolute_url(self):
        return ('expense_type_detail', (smart_unicode(self.id),))

class ExpenseManager(models.Manager):
    def for_timesheet(self, timesheet):
        """
        Creates a ``QuerySet`` containing all Expenses associated with
        the given Timesheet, giving each Expense additional Expense Type
        and Job details as required for display when editing a complete
        Timesheet.
        """
        opts = self.model._meta
        job_opts = Job._meta
        expense_type_opts = ExpenseType._meta
        job_table = qn(job_opts.db_table)
        expense_type_table = qn(expense_type_opts.db_table)
        return super(ExpenseManager, self).get_query_set().filter(timesheet=timesheet).extra(
            select={
                'job_number': '%s.%s' % (job_table, qn(job_opts.get_field('number').column)),
                'job_name': '%s.%s' % (job_table, qn(job_opts.get_field('name').column)),
                'type_name': '%s.%s' % (expense_type_table, qn(expense_type_opts.get_field('name').column)),
            },
            tables=[job_table, expense_type_table],
            where=[
                '%s.%s = %s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('job').column),
                    job_table,
                    qn(job_opts.pk.column),
                ),
                '%s.%s = %s.%s' % (
                    qn(opts.db_table),
                    qn(opts.get_field('type').column),
                    expense_type_table,
                    qn(expense_type_opts.pk.column),
                ),
            ]
        )

    def bulk_approve(self, user, start_date, end_date):
        """
        Marks all unapproved Expenses between the given dates as
        approved by the given User and returns the number of rows
        updated.
        """
        opts = self.model._meta
        query = """
        UPDATE %(expense)s
        SET %(approved_by)s = %%s
        WHERE %(date)s >= %%s
          AND %(date)s <= %%s
          AND %(approved_by)s IS NULL""" % {
            'expense': qn(opts.db_table),
            'approved_by': qn(opts.get_field('approved_by').column),
            'date': qn(opts.get_field('date').column),
        }
        cursor = connection.cursor()
        cursor.execute(query, [user.id, start_date, end_date])
        return cursor.rowcount

class Expense(models.Model):
    """
    An expense incurred while working on a Job.
    """
    timesheet   = models.ForeignKey(Timesheet, related_name='expenses', edit_inline=models.TABULAR)
    user        = models.ForeignKey(User, related_name='expenses')
    job         = models.ForeignKey(Job, related_name='expenses', core=True)
    type        = models.ForeignKey(ExpenseType, related_name='expenses', core=True)
    date        = models.DateField()
    amount      = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=100, blank=True)
    billable    = models.BooleanField(default=True)

    # Administration
    approved_by = models.ForeignKey(User, null=True, blank=True, related_name='approved_expenses')
    invoice     = models.ForeignKey(Invoice, null=True, blank=True, related_name='expenses')

    objects = ExpenseManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.type.name, self.job.name)

    class Meta:
        ordering = ['-date']

    class Admin:
        list_display = ('timesheet', 'user', 'job', 'type', 'date', 'amount',
                        'description', 'billable', 'approved_by', 'invoice')

    def is_editable(self):
        return self.approved_by_id is None and self.invoice_id is None

    def is_approved(self):
        return self.invoice_id is None and self.approved_by_id is not None

    def is_invoiced(self):
        return self.invoice_id is not None

    def is_deleteable(self):
        return self.is_editable()

###########
# Reports #
###########

class SQLReportManager(models.Manager):
    def accessible_to_user(self, user):
        """
        Creates a ``QuerySet`` containing SQL Reports the given User may
        access based on their role.
        """
        user_profile = user.get_profile()
        qs = super(SQLReportManager, self).get_query_set()
        if user_profile.is_admin():
            pass
        elif user_profile.is_manager():
            qs = qs.filter(access__in=['M','U'])
        elif user_profile.is_user():
            qs = qs.filter(access='U')
        return qs

class SQLReport(models.Model):
    """
    A custom report defined using SQL.
    """
    name   = models.CharField(max_length=100, unique=True)
    access = models.CharField(max_length=1, choices=ACCESS_CHOICES)
    query  = models.TextField(validator_list=[isSafeishQuery])

    objects = SQLReportManager()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'SQL report'
        ordering = ['name']

    class Admin:
        list_display = ('name', 'access')
        list_filter = ('access',)

    @models.permalink
    def get_absolute_url(self):
        return ('sql_report_detail', (smart_unicode(self.id),))

    def get_sql_parameters(self):
        return set(sql_param_re.findall(self.query))

    def get_populated_query(self, params):
        query = self.query
        for param, value in params.items():
            query = query.replace(u'::%s' % param, value)
        return query

    def get_headings_from_query(self):
        return heading_re.findall(self.query)
