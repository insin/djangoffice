from django import newforms as forms
from django.contrib.auth.models import User

from djangoffice.models import UserProfile

class AdminUserForm(forms.Form):
    username   = forms.CharField(max_length=30)
    first_name = forms.CharField(max_length=30)
    last_name  = forms.CharField(max_length=30)
    email      = forms.EmailField()
    password   = forms.CharField(required=False, widget=forms.PasswordInput())
    confirm    = forms.CharField(required=False, widget=forms.PasswordInput())

    def clean_confirm(self):
        if self.cleaned_data.get('password') and \
           not self.cleaned_data.get('confirm') or \
           self.cleaned_data['password'] != self.cleaned_data['confirm']:
            raise forms.ValidationError(u'Please ensure your passwords match.')
        return self.cleaned_data['confirm']

USER_ROLE_CHOICES = tuple([choice for choice in UserProfile.ROLE_CHOICES \
                           if choice[0] != UserProfile.ADMINISTRATOR_ROLE])

class UserForm(forms.Form):
    role          = forms.ChoiceField(choices=USER_ROLE_CHOICES)
    first_name    = forms.CharField(max_length=30)
    last_name     = forms.CharField(max_length=30)
    username      = forms.CharField(max_length=30)
    email         = forms.EmailField()
    phone_number  = forms.CharField(required=False, max_length=30)
    mobile_number = forms.CharField(required=False, max_length=30)
    password      = forms.CharField(widget=forms.PasswordInput())
    confirm       = forms.CharField(widget=forms.PasswordInput())
    disabled      = forms.BooleanField(required=False)
    managed_users = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['managed_users'].choices = [(u.id, u.get_full_name()) \
            for u in User.objects.filter(userprofile__role=UserProfile.USER_ROLE)]

    def clean_confirm(self):
        if self.cleaned_data.get('password') and \
           not self.cleaned_data.get('confirm') or \
           self.cleaned_data['password'] != self.cleaned_data['confirm']:
            raise forms.ValidationError(
                u'Please make sure your passwords match.')
        return self.cleaned_data['confirm']

    def clean_managed_users(self):
        if self.cleaned_data.get('role') and \
           self.cleaned_data.get('managed_users') and \
           self.cleaned_data['role'] not in [UserProfile.PM_ROLE,
                                             UserProfile.MANAGER_ROLE] and \
           len(self.cleaned_data['managed_users']) > 0:
            raise forms.ValidationError(
                u'Only Managers and PMs may have managed users.')
        return self.cleaned_data['managed_users']

    def clean_username(self):
        if self.cleaned_data.get('username'):
            try:
                User.objects.get(username=self.cleaned_data['username'])
            except User.DoesNotExist:
                return self.cleaned_data['username']
            raise forms.ValidationError(
                u'The username "%s" is already taken.' \
                % self.cleaned_data['username'])

class EditUserForm(UserForm):
    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        # Username is not updateable
        self.fields['username'].required = False
        self.fields['username'].widget.attrs['disabled'] = 'disabled'
        # Password is now only required if being changed
        self.fields['password'].required = False
        self.fields['confirm'].required = False
