import operator

from django import newforms as forms
from django.contrib.auth.models import User
from django.db.models.query import Q

from officeaid.forms import FilterBaseForm
from officeaid.forms.fields import (DynamicModelChoiceField,
    MultipleDynamicModelChoiceField)
from officeaid.models import Client, Contact, Job, Task, UserProfile

SEARCH_TYPE_CHOICES = (
    (1, u'Job Number'),
    (2, u'Job Name'),
    (3, u'Primary Contact Name'),
    (4, u'Billing Address Contact Name'),
    (5, u'Job Contact Name'),
)

USER_SEARCH_TYPE_CHOICES = (
    (1, u'Director'),
    (2, u'Project Coordinator'),
    (3, u'Project Manager'),
    (4, u'Architect'),
    (5, u'Assigned to Job Task'),
)

JOB_STATUS_SEARCH_CHOICES = ((u'', u'All Jobs'),) + Job.STATUS_CHOICES

DATE_SEARCH_TYPE_CHOICES = (
    (1, 'Start Date'),
    (2, 'Expected End Date'),
)

class JobFilterForm(FilterBaseForm, forms.Form):
    """
    A form for Job search criteria.
    """
    search           = forms.CharField(required=False)
    search_type      = forms.IntegerField(required=False, widget=forms.Select(choices=SEARCH_TYPE_CHOICES))
    user             = forms.ChoiceField(required=False)
    user_search_type = forms.IntegerField(required=False, widget=forms.Select(choices=USER_SEARCH_TYPE_CHOICES))
    status           = forms.ChoiceField(required=False, choices=JOB_STATUS_SEARCH_CHOICES)
    client           = forms.ChoiceField(required=False)
    date_search_type = forms.IntegerField(required=False, widget=forms.Select(choices=DATE_SEARCH_TYPE_CHOICES))
    start_date       = forms.DateField(required=False)
    end_date         = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        super(JobFilterForm, self).__init__(*args, **kwargs)
        self.fields['user'].choices = [(u'', '---------')] + \
            [(u.id, u.get_full_name()) \
             for u in User.objects.exclude(userprofile__role=UserProfile.ADMINISTRATOR_ROLE)]
        self.fields['client'].choices = [(u'', '---------')] + \
            [(c.id, c.name) for c in Client.objects.all()]
        self.make_distinct = False

    def get_filters(self):
        """
        Creates a ``Q`` object defining search criteria based on the
        contents of this form.

        Returns ``None``If the form is invalid or no searchcriteria were
        provided.
        """
        if not self.is_valid():
            return None
        filters = []

        # General search
        if self.cleaned_data['search']:
            search_value = self.cleaned_data['search']
            search_type = self.cleaned_data['search_type']
            if search_type == 1:
                filters.append(Q(name__icontains=search_value))
            elif search_type == 2:
                filters.append(Q(number=search_value))
            elif search_type == 3:
                filters.append(
                    Q(primary_contact__first_name__icontains=search_value) | \
                    Q(primary_contact__last_name__icontains=search_value))
            elif search_type == 4:
                filters.append(
                    Q(billing_contact__first_name__icontains=search_value) | \
                    Q(billing_contact__last_name__icontains=search_value))
            elif search_type == 5:
                filters.append(
                    Q(job_contacts__first_name__icontains=search_value) | \
                    Q(job_contacts__last_name__icontains=search_value))
                self.make_distinct = True

        # User search
        if self.cleaned_data['user']:
            search_user = self.cleaned_data['user']
            user_search_type = self.cleaned_data['user_search_type']
            if user_search_type == 1:
                filters.append(Q(director=search_user))
            elif user_search_type == 2:
                filters.append(Q(project_coordinator=search_user))
            elif user_search_type == 3:
                filters.append(Q(project_manager=search_user))
            elif user_search_type == 4:
                filters.append(Q(architect=search_user))
            elif user_search_type == 5:
                filters.append(Q(tasks__assigned_users=search_user))
                self.make_distinct = True

        # Status search
        if self.cleaned_data['status']:
            filters.append(Q(status=self.cleaned_data['status']))

        # Client search
        if self.cleaned_data['client']:
            filters.append(Q(client=self.cleaned_data['client']))

        # Date search
        date_search_type = self.cleaned_data['date_search_type']
        if self.cleaned_data['start_date']:
            start_date = self.cleaned_data['start_date']
            if date_search_type == 1:
                filters.append(Q(start_date__gte=start_date))
            if date_search_type == 2:
                filters.append(Q(end_date__gte=start_date))
        if self.cleaned_data['end_date']:
            end_date = self.cleaned_data['end_date']
            if date_search_type == 1:
                filters.append(Q(start_date__lte=end_date))
            if date_search_type == 2:
                filters.append(Q(end_date__lte=end_date))

        if len(filters) == 0:
            return None
        else:
            return reduce(operator.and_, filters)

class AddJobForm(forms.Form):
    """
    A form for adding a new Job.
    """
    client              = forms.ModelChoiceField(queryset=Client.objects.all())
    name                = forms.CharField(max_length=100)
    number              = forms.IntegerField(required=False, min_value=1)
    reference           = forms.CharField(required=False, max_length=16)
    reference_date      = forms.DateField(required=False)
    add_reference       = forms.CharField(required=False, max_length=16)
    add_reference_date  = forms.DateField(required=False)
    status              = forms.ChoiceField(choices=Job.STATUS_CHOICES)
    notes               = forms.CharField(required=False, widget=forms.Textarea())
    invoice_notes       = forms.CharField(required=False, widget=forms.Textarea())
    director            = forms.ModelChoiceField(queryset=User.objects.filter(userprofile__role=UserProfile.MANAGER_ROLE))
    project_coordinator = forms.ModelChoiceField(queryset=User.objects.filter(userprofile__role=UserProfile.MANAGER_ROLE))
    project_manager     = forms.ModelChoiceField(queryset=User.objects.exclude(userprofile__role=UserProfile.ADMINISTRATOR_ROLE))
    architect           = forms.ModelChoiceField(queryset=User.objects.exclude(userprofile__role=UserProfile.ADMINISTRATOR_ROLE))
    primary_contact     = DynamicModelChoiceField(Contact)
    billing_contact     = DynamicModelChoiceField(Contact)
    job_contacts        = MultipleDynamicModelChoiceField(Contact, required=False)
    start_date          = forms.DateField(required=False)
    end_date            = forms.DateField(required=False)
    fee_basis           = forms.ChoiceField(required=False, choices=Job.FEE_BASIS_CHOICES)
    fee_amount          = forms.DecimalField(required=False, max_digits=8, decimal_places=2)
    fee_currency        = forms.ChoiceField(choices=Job.FEE_CURRENCY_CHOICES)
    contingency         = forms.DecimalField(required=False, max_digits=6, decimal_places=2)

    def __init__(self, users, *args, **kwargs):
        super(AddJobForm, self).__init__(*args, **kwargs)
        self.fields['client'].choices = [(client['id'], client['name']) \
            for client in Client.objects.values('id', 'name')]
        self.fields['director'].choices = \
            self.fields['project_coordinator'].choices = \
            [(u.pk, u.get_full_name()) for u in \
             User.objects.filter(userprofile__role=UserProfile.MANAGER_ROLE)]
        self.fields['project_manager'].choices = \
            self.fields['architect'].choices = [(u.pk, u.get_full_name()) \
                                                for u in users]

    def clean_number(self):
        if self.cleaned_data['number']:
            if Job.objects.filter(number=self.cleaned_data['number']).count():
                raise forms.ValidationError(u'This number is already in use.')
        return self.cleaned_data['number']

    def clean_end_date(self):
        if self.cleaned_data['start_date'] and self.cleaned_data['end_date']:
            if self.cleaned_data['end_date'] < self.cleaned_data['start_date']:
                raise forms.ValidationError(
                    u'If given, this field must be later than or equal to Start Date.')
        return self.cleaned_data['end_date']

    def clean_fee_amount(self):
        if 'fee_basis' in self.cleaned_data and \
           self.cleaned_data['fee_amount'] is None:
            if self.cleaned_data['fee_basis'] in [Job.SET_FEE, Job.PERCENTAGE_FEE]:
                raise forms.ValidationError(
                    u'This field is required if Fee Basis is %s.' \
                    % dict(Job.FEE_BASIS_CHOICES)[self.cleaned_data['fee_basis']])
        return self.cleaned_data['fee_amount']

    def save(self, commit=True):
        return forms.save_instance(self, Job(), self.fields, commit=commit)

class AddTaskForm(forms.Form):
    """
    A form for adding a new Task.

    Since a Job may have multiple Jobs, but only one Task with a given
    Task Type, this form will automatically be prefixed with the Task's
    Task Type id.
    """
    add            = forms.BooleanField(required=False)
    assigned_users = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={'size': 4}))
    estimate_hours = forms.DecimalField(max_digits=6, decimal_places=2, min_value=0, required=False)
    start_date     = forms.DateField(required=False)
    end_date       = forms.DateField(required=False)

    def __init__(self, task_type, user_choices, *args, **kwargs):
        kwargs['prefix'] = 'task%s' % task_type.id
        super(AddTaskForm, self).__init__(*args, **kwargs)
        self.fields['assigned_users'].choices = user_choices
        self.task_type = task_type

    def clean_assigned_users(self):
        if self.cleaned_data['add']:
            if not self.cleaned_data.get('assigned_users') or \
               len(self.cleaned_data['assigned_users']) == 0:
                raise forms.ValidationError(
                    u'You must assign at least one user.')
        return self.cleaned_data['assigned_users']

    def clean_estimate_hours(self):
        if self.cleaned_data['add'] and not \
           self.cleaned_data['estimate_hours']:
            raise forms.ValidationError(u'You must provide an estimate.')
        return self.cleaned_data['estimate_hours']

    def clean_end_date(self):
        if self.cleaned_data.get('start_date', None) and \
           self.cleaned_data.get('end_date', None):
            if self.cleaned_data['end_date'] < self.cleaned_data['start_date']:
                raise forms.ValidationError(
                    u'Must be later than or equal to start date.')
        return self.cleaned_data['end_date']

    def save(self, job):
        task = Task.objects.create(job=job, task_type=self.task_type,
            estimate_hours=self.cleaned_data['estimate_hours'],
            start_date=self.cleaned_data['start_date'],
            end_date=self.cleaned_data['end_date'])
        task.assigned_users = self.cleaned_data['assigned_users']
        return task

class EditJobForm(AddJobForm):
    """
    A form for editing a Job.
    """
    def __init__(self, job, users, *args, **kwargs):
        super(EditJobForm, self).__init__(users, *args, **kwargs)
        del self.fields['number']
        self.job = job
        opts = Job._meta
        for f in opts.fields + opts.many_to_many:
            if not f.name in self.fields:
                continue
            self.fields[f.name].initial = f.value_from_object(job)

    def save(self, commit=True):
        return forms.save_instance(self, self.job, commit=commit)

class EditTaskForm(forms.Form):
    """
    A form for editing a Task.

    Since a Job may have multiple Jobs, but only one Task with a given
    Task Type, this form will automatically be prefixed with the Task's
    Task Type id.
    """
    assigned_users = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={'size': 4}))
    estimate_hours = forms.DecimalField(max_digits=6, decimal_places=2, min_value=0, required=False)
    start_date     = forms.DateField(required=False)
    end_date       = forms.DateField(required=False)

    def __init__(self, task, user_choices, *args, **kwargs):
        kwargs['prefix'] = 'task%s' % task.task_type_id
        super(EditTaskForm, self).__init__(*args, **kwargs)
        self.fields['assigned_users'].choices = user_choices
        self.fields['assigned_users'].initial = \
            [user['id'] for user in task.assigned_users.values('id')]
        self.fields['estimate_hours'].initial = task.estimate_hours
        self.fields['start_date'].initial = task.start_date
        self.fields['end_date'].initial = task.end_date
        self.task = task

    def clean_assigned_users(self):
        if not self.cleaned_data.get('assigned_users') or \
           len(self.cleaned_data['assigned_users']) == 0:
            raise forms.ValidationError(
                u'You must assign at least one user.')
        return self.cleaned_data['assigned_users']

    def clean_estimate_hours(self):
        if not self.cleaned_data['estimate_hours']:
            raise forms.ValidationError(u'You must provide an estimate.')
        return self.cleaned_data['estimate_hours']

    def clean_end_date(self):
        if self.cleaned_data.get('start_date', None) and \
           self.cleaned_data.get('end_date', None):
            if self.cleaned_data['end_date'] < self.cleaned_data['start_date']:
                raise forms.ValidationError(
                    u'Must be later than or equal to start date.')
        return self.cleaned_data['end_date']

    def save(self):
        self.task.assigned_users = self.cleaned_data['assigned_users']
        self.task.estimate_hours= self.cleaned_data['estimate_hours']
        self.task.start_date = self.cleaned_data['start_date']
        self.task.end_date = self.cleaned_data['end_date']
        self.task.save()
        return self.task
