from django import newforms as forms
from django.contrib.auth.models import User

from officeaid.forms import FilterBaseForm

class ActivityFilterForm(FilterBaseForm, forms.Form):
    SEARCH_FILTERS = (
        ('job_number', 'job__number'),
        ('creator', 'created_by__pk'),
        ('assigned_to', 'assigned_to__pk'),
        ('contact', 'contact__pk'),
    )

    job_number  = forms.IntegerField(required=False)
    creator     = forms.ChoiceField(required=False)
    assigned_to = forms.ChoiceField(required=False)
    contact     = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(ActivityFilterForm, self).__init__(*args, **kwargs)
        user_choices = [('', '-' * 9)] + \
            [(u.id, u.get_full_name()) \
             for u in User.objects.exclude(userprofile__role='A')]
        self.fields['creator'].choices = user_choices
        self.fields['assigned_to'].choices = user_choices