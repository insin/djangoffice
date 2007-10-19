from django import newforms as forms
from django.contrib.auth.models import User

from officeaid.forms import FilterBaseForm
from officeaid.forms.fields import DynamicModelChoiceField
from officeaid.models import ActivityType, Contact

class ActivityFilterForm(FilterBaseForm, forms.Form):
    SEARCH_FILTERS = (
        ('job_number',  'job__number'),
        ('type',        'type__pk'),
        ('creator',     'created_by__pk'),
        ('assigned_to', 'assigned_to__pk'),
        ('contact',     'contact__pk'),
    )

    job_number  = forms.IntegerField(required=False)
    type        = forms.ChoiceField(required=False)
    creator     = forms.ChoiceField(required=False)
    assigned_to = forms.ChoiceField(required=False)
    contact     = DynamicModelChoiceField(Contact, required=False)

    def __init__(self, *args, **kwargs):
        super(ActivityFilterForm, self).__init__(*args, **kwargs)
        self.fields['type'].choices = \
            [('', '-' * 9)] + [(a.pk, a.name) \
                               for a in ActivityType.objects.all()]
        self.fields['creator'].choices = self.fields['assigned_to'].choices = \
            [('', '-' * 9)] + [(u.pk, u.get_full_name()) \
                               for u in User.objects.exclude(userprofile__role='A')]
