from urllib import quote

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect

from officeaid import models
from officeaid.views import permission_denied

def user_has_role(roles):
    """
    Creates a function which validates that a given user has one of the
    given roles.
    """
    def _check_role(user):
        return user.is_authenticated() and user.get_profile().role in roles
    return _check_role

# Authentication and permission test functions
is_authenticated = lambda u: u.is_authenticated()
is_not_authenticated = lambda u: not u.is_authenticated()
is_admin = user_has_role(['A'])
is_admin_or_manager = user_has_role(['A', 'M'])

def user_can_access_user(logged_in_user, user):
    """
    Validates that the given logged in user has permission to access
    another user's details throughout the application.
    """
    if logged_in_user.id == user.id:
        # Everyone can access their own details
        return True

    profile = logged_in_user.get_profile()
    if profile.is_user():
        return False # Users may only access their own details
    elif profile.is_admin():
        return True  # Admins can access everyone
    elif profile.is_manager():
        if models.access.managers_view_all_users:
            return True # Managers can access everyone when the
                        # appropriate setting is enabled.
        else:
            # Otherwise, managers can only access their managed users
            try:
                profile.managed_users.get(id=user.id)
                return True
            except:
                return False

def user_has_permission(test_func):
    """
    Decorator for view functions which validates that the current User
    is authenticated and passes a permission check before the view
    function is executed.

    If the current user is not logged in, they are redirected to the
    login screen.

    If the current user does not have permission to access the view
    function in question, the ``permission_denied`` view function is
    executed instead.
    """
    def _dec(view_func):
        def _checkuser(request, *args, **kwargs):
            if request.user.is_authenticated():
                if test_func(request.user):
                    return view_func(request, *args, **kwargs)
                return permission_denied(request)
            return HttpResponseRedirect('%s?%s=%s' % (settings.LOGIN_URL, REDIRECT_FIELD_NAME, quote(request.get_full_path())))
        _checkuser.__doc__ = view_func.__doc__
        _checkuser.__dict__ = view_func.__dict__
        return _checkuser
    return _dec
