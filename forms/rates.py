from django import newforms as forms

from djangoffice.models import TaskTypeRate, UserRate

class EditRateForm(forms.Form):
    standard_rate = forms.DecimalField(max_digits=6, decimal_places=2, min_value=0)
    overtime_rate = forms.DecimalField(max_digits=6, decimal_places=2, min_value=0)

    def __init__(self, rate, *args, **kwargs):
        self.rate = rate
        super(EditRateForm, self).__init__(*args, **kwargs)
        self.fields['standard_rate'].initial = rate.standard_rate
        self.fields['overtime_rate'].initial = rate.overtime_rate

class UserRateBaseForm(forms.BaseForm):
    def __init__(self, user, *args, **kwargs):
        super(UserRateBaseForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_effective_from(self):
        if self.cleaned_data['effective_from']:
            latest = UserRate.objects.get_latest_effective_from_for_user(self.user)
            if not latest or self.cleaned_data['effective_from'] > latest:
                return self.cleaned_data['effective_from']
            else:
                raise forms.ValidationError(
                    u'Effective from date must be later than those of existing rates.')

class TaskTypeRateBaseForm(forms.BaseForm):
    def __init__(self, task_type, *args, **kwargs):
        self.task_type = task_type
        super(TaskTypeRateBaseForm, self).__init__(*args, **kwargs)

    def clean_effective_from(self):
        if self.cleaned_data['effective_from']:
            latest = TaskTypeRate.objects.get_latest_effective_from_for_task_type(self.task_type)
            if not latest or self.cleaned_data['effective_from'] > latest:
                return self.cleaned_data['effective_from']
            else:
                raise forms.ValidationError(
                    u'Effective from date must be later than those of existing rates.')