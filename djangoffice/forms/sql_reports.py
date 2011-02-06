from django import forms

class SQLReportParameterForm(forms.Form):
    def __init__(self, param_names, *args, **kwargs):
        super(SQLReportParameterForm, self).__init__(*args, **kwargs)
        for name in param_names:
            self.fields[name] = forms.CharField()
