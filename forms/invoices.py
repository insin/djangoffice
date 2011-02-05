from django import newforms as forms
from django.contrib.auth.models import User
from django.template.defaultfilters import pluralize

from djangoffice.forms import FilterBaseForm, HiddenBaseForm
from djangoffice.forms.widgets import TableSelectMultiple
from djangoffice.models import Invoice

class InvoiceFilterForm(FilterBaseForm, forms.Form):
    pass

class SelectJobsForInvoiceForm(HiddenBaseForm, forms.Form):
    """
    A Form which handles selection of Jobs for invoice.
    """
    jobs = forms.MultipleChoiceField(widget=TableSelectMultiple(
        item_attrs=('formatted_number', 'name', 'client',
                    'get_status_display')))

    def __init__(self, accessible_jobs, *args, **kwargs):
        super(SelectJobsForInvoiceForm, self).__init__(*args, **kwargs)
        self.fields['jobs'].choices = [(j.id, j) \
                                       for j in accessible_jobs]

    def clean(self):
        if 'jobs' not in self.cleaned_data or \
           len(self.cleaned_data['jobs']) == 0:
            raise forms.ValidationError(
                u'You must select at least one Job for invoice.')
        return self.cleaned_data

class InvoiceCriteriaForm(HiddenBaseForm, forms.Form):
    """
    A Form which handles invoice critieria for a single Job or multiple
    Jobs.
    """
    type                         = forms.ChoiceField(choices=Invoice.TYPE_CHOICES)
    date                         = forms.DateField()
    start_period                 = forms.DateField(required=False)
    end_period                   = forms.DateField(required=False)
    show_hours_booked_by_date    = forms.BooleanField(required=False, initial=True)
    show_tasks_by_user           = forms.BooleanField(required=False, initial=True)
    show_tasks_summary           = forms.BooleanField(required=False, initial=True)
    show_expenses_by_user        = forms.BooleanField(required=False, initial=True)
    show_expenses_summary        = forms.BooleanField(required=False, initial=True)
    show_final_totals            = forms.BooleanField(required=False, initial=True)
    show_financials              = forms.BooleanField(required=False, initial=True)
    total_amount                 = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    additional_hours             = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    additional_hours_cost        = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    additional_hours_description = forms.CharField(required=False)
    extra_expense_amount         = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    extra_expense_description    = forms.CharField(required=False)
    extra_expense_override       = forms.BooleanField(required=False)

    def __init__(self, jobs, *args, **kwargs):
        """
        Dynamically creates fields to allow manual entry of an invoice
        number for each Job to be invoiced.
        """
        self.jobs = jobs
        super(InvoiceCriteriaForm, self).__init__(*args, **kwargs)
        for job in jobs:
            self.fields['number%s' % job.id] = forms.IntegerField(
                required=False, label=unicode(job))

    def clean(self):
        """
        Validates that any manual invoice numbers given are not already
        in use.
        """
        numbers = [self.cleaned_data['number%s' % job.id] \
                   for job in self.jobs \
                   if self.cleaned_data['number%s' % job.id] is not None]
        if len(numbers) > 0:
            existing_numbers = [invoice.formatted_number for invoice \
                                in Invoice.objects.filter(number__in=numbers)]
            if len(existing_numbers) > 0:
                raise forms.ValidationError(
                    u'The following invoice number%s already in use: %s' \
                    % (pluralize(len(existing_numbers), u' is,s are'),
                       u', '.join(existing_numbers)))
        return self.cleaned_data

    def clean_start_period(self):
        if 'type' in self.cleaned_data and \
           self.cleaned_data['type'] == Invoice.DATE_RESTRICTED_TYPE and \
           self.cleaned_data['start_period'] is None:
            raise forms.ValidationError('Required if invoice type is %s.' \
                                        % dict(Invoice.TYPE_CHOICES)[Invoice.DATE_RESTRICTED_TYPE])

    def clean_end_period(self):
        if 'type' in self.cleaned_data and \
           self.cleaned_data['type'] == Invoice.DATE_RESTRICTED_TYPE and \
           self.cleaned_data['end_period'] is None:
            raise forms.ValidationError('Required if invoice type is %s.' \
                                        % dict(Invoice.TYPE_CHOICES)[Invoice.DATE_RESTRICTED_TYPE])

    def clean_additional_hours_cost(self):
        if self.cleaned_data['additional_hours'] is not None and \
           self.cleaned_data['additional_hours_cost'] is None:
            raise forms.ValidationError(
                'Required if additional hours are given.')

    def clean_additional_hours_description(self):
        if self.cleaned_data['additional_hours'] is not None and \
           self.cleaned_data['additional_hours_description'] in (None, u''):
            raise forms.ValidationError(
                'Required if additional hours are given.')

    def clean_extra_expense_description(self):
        if self.cleaned_data['extra_expense_amount'] is not None and  \
           self.cleaned_data['extra_expense_description'] in (None, u''):
            raise forms.ValidationError(
                'Required if an extra expense amount is given.')
