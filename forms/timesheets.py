from django import newforms as forms
from officeaid.forms.widgets import DateInput, HourInput, MoneyInput
from officeaid.models import Expense, ExpenseType, Task, TimeEntry
from officeaid.utils.dates import week_ending_date

class BulkApprovalForm(forms.Form):
    """
    Form for bulk approval of timesheet items based on a date range.
    """
    start_date = forms.DateField(widget=DateInput())
    end_date   = forms.DateField(widget=DateInput())

    def clean_end_date(self):
        if self.cleaned_data.get('start_date') and \
           self.cleaned_data.get('end_date'):
            if not self.cleaned_data['end_date'] >= \
               self.cleaned_data['start_date']:
                raise forms.ValidationError(
                    u'Must be later than or equal to Start Date.')
        return self.cleaned_data['end_date']

################
# Time Entries #
################

class AddTimeEntryForm(forms.Form):
    """
    Form for addition of Time Entries.
    """
    job         = forms.ChoiceField()
    task        = forms.ChoiceField()
    mon         = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    tue         = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    wed         = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    thu         = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    fri         = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    sat         = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    sun         = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    overtime    = forms.DecimalField(max_digits=4, decimal_places=2, required=False, widget=HourInput())
    description = forms.CharField(max_length=100, required=False)

    def __init__(self, jobs, tasks=None, *args, **kwargs):
        super(AddTimeEntryForm, self).__init__(*args, **kwargs)
        self.fields['job'].choices = [(u'', u'----------')] + \
            [(j.id, u'%s - %s' % (j.formatted_number, j.name)) \
             for j in jobs]
        self.fields['task'].choices = [(u'', u'----------')]
        if tasks:
            self.fields['task'].choices += [(t.id, t.task_type_name) \
                                            for t in tasks]

    def save(self, timesheet=None, commit=True):
        instance = TimeEntry()
        for f in instance._meta.fields:
            if f.name not in self.fields:
                continue
            setattr(instance, f.name, self.cleaned_data[f.name])
        instance.job_id = self.cleaned_data['job']
        instance.task_id = self.cleaned_data['task']
        if timesheet:
            instance.timesheet = timesheet
        if commit:
            instance.save()
        return instance

class EditTimeEntryForm(AddTimeEntryForm):
    """
    Form for editing Time Entries.

    If the current user has the authority to approve the Time Entry
    being edited, this form will contain an ``approved`` field in
    addition to the fields defined in ``AddTimeEntryForm``.
    """
    def __init__(self, time_entry, jobs, tasks=None, can_approve=False, *args,
                 **kwargs):
        self.time_entry, self.can_approve = time_entry, can_approve
        super(EditTimeEntryForm, self).__init__(jobs, tasks=tasks, *args,
                                                **kwargs)
        if can_approve:
            self.fields['approved'] = forms.BooleanField(required=False)
        self.fields['job'].initial = time_entry.job_id
        self.fields['task'].initial = time_entry.task_id
        for f in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'overtime',
                  'description']:
            self.fields[f].initial = getattr(time_entry, f)

    def save(self, user, commit=True):
        """
        user
            The user initiating the save.
        """
        for f in self.time_entry._meta.fields:
            if f.name not in self.fields:
                continue
            setattr(self.time_entry, f.name, self.cleaned_data[f.name])
        self.time_entry.job_id = self.cleaned_data['job']
        self.time_entry.task_id = self.cleaned_data['task']
        if self.can_approve and self.cleaned_data['approved']:
            self.time_entry.approved_by = user
        if commit:
            self.time_entry.save()
        return self.time_entry

class ApprovedTimeEntryForm(forms.Form):
    """
    Form for editing approved Time Entries.

    The only operation which may be performed on an approved, uninvoiced
    Time Entry is an unapprove.
    """
    approved = forms.BooleanField(initial=True, required=False)

    def __init__(self, time_entry, can_approve, *args, **kwargs):
        self.time_entry, self.can_approve = time_entry, can_approve
        super(ApprovedTimeEntryForm, self).__init__(*args, **kwargs)

    def save(self, user, commit=True):
        """
        user
            The user initiating the save.
        """
        if self.time_entry.approved_by_id and not \
           self.cleaned_data['approved']:
            self.time_entry.approved_by = None
            if commit:
                self.time_entry.save()
        return self.time_entry

############
# Expenses #
############

class AddExpenseForm(forms.Form):
    """
    Form for addition of Expenses.
    """
    job         = forms.ChoiceField()
    type        = forms.ChoiceField()
    date        = forms.DateField(widget=DateInput())
    amount      = forms.DecimalField(max_digits=8, decimal_places=2, widget=MoneyInput())
    description = forms.CharField(max_length=100, required=False)
    billable    = forms.BooleanField(initial=True, required=False)

    def __init__(self, jobs, week_commencing, expense_types=None, *args,
                 **kwargs):
        super(AddExpenseForm, self).__init__(*args, **kwargs)
        self.fields['job'].choices = [(u'', u'----------')] + \
            [(j.id, u'%s - %s' % (j.formatted_number, j.name)) \
             for j in jobs]
        if expense_types is None:
            expense_types = ExpenseType.objects.all()
        self.fields['type'].choices = [(u'', u'----------')] + \
            [(et.id, et.name) for et in expense_types]
        self.week_commencing = week_commencing

    def clean_date(self):
        if self.cleaned_data['date'] >= self.week_commencing and \
           self.cleaned_data['date'] <= week_ending_date(self.week_commencing):
            return self.cleaned_data['date']
        raise forms.ValidationError(
            u'Must occur during the selected timesheet\'s period.')

    def save(self, timesheet=None, commit=True):
        instance = Expense()
        for f in instance._meta.fields:
            if f.name not in self.fields:
                continue
            setattr(instance, f.name, self.cleaned_data[f.name])
        instance.job_id = self.cleaned_data['job']
        instance.type_id = self.cleaned_data['type']
        if timesheet:
            instance.timesheet = timesheet
        if commit:
            instance.save()
        return instance

class EditExpenseForm(AddExpenseForm):
    """
    Form for editing Expenses.

    If the current user has the authority to approve the Expense being
    edited, this form will  contain an ``approved`` field in addition to
    the fields defined in ``AddExpenseForm``.
    """
    def __init__(self, expense, jobs, expense_types, week_commencing,
                 can_approve=False, *args, **kwargs):
        self.expense, self.can_approve = expense, can_approve
        super(EditExpenseForm, self).__init__(jobs, week_commencing,
                                              expense_types, *args, **kwargs)
        if can_approve:
            self.fields['approved'] = forms.BooleanField(required=False)
        self.fields['job'].initial = expense.job_id
        self.fields['type'].initial = expense.type_id
        for f in ['date', 'amount', 'description', 'billable']:
            self.fields[f].initial = getattr(expense, f)

    def save(self, user, commit=True):
        """
        user
            The user initiating the save.
        """
        for f in self.expense._meta.fields:
            if f.name not in self.fields:
                continue
            setattr(self.expense, f.name, self.cleaned_data[f.name])
        self.expense.job_id = self.cleaned_data['job']
        self.expense.type_id = self.cleaned_data['type']
        if self.can_approve and self.cleaned_data['approved']:
            self.expense.approved_by = user
        if commit:
            self.expense.save()
        return self.expense

class ApprovedExpenseForm(forms.Form):
    """
    Form for editing approved Expenses.

    The only operation which may be performed on an approved, uninvoiced
    Expense is an unapprove.
    """
    approved = forms.BooleanField(initial=True, required=False)

    def __init__(self, expense, can_approve, *args, **kwargs):
        self.expense, self.can_approve = expense, can_approve
        super(ApprovedExpenseForm, self).__init__(*args, **kwargs)

    def save(self, user, commit=True):
        """
        user
            The user initiating the save.
        """
        if self.expense.approved_by_id and not self.cleaned_data['approved']:
            self.expense.approved_by = None
            if commit:
                self.expense.save()
        return self.expense
