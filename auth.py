"""
Functions which may be used to enforce role-based authorisation, based on
the ``role`` attribute in each user's ``UserProfile``.

Access to other users
=====================

The rules for the logged-in user accessing other users' details are as
follows, as implemented in the ``user_can_access_user`` and
``get_accessible_users`` functions.

* Admins have unrestricted access to all users.
* Managers can access everyone but admins when the appropriate system
  setting is enabled; otherwise, they can access their managed users.
* Project coordinators can access their managed users.
* Users can only access their own details.
"""
from urllib import quote

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from officeaid import models
from officeaid.models import UserProfile

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
is_admin = user_has_role([UserProfile.ADMINISTRATOR_ROLE])
is_admin_or_manager = user_has_role([UserProfile.ADMINISTRATOR_ROLE,
                                     UserProfile.MANAGER_ROLE])
is_admin_manager_or_pc = user_has_role([UserProfile.ADMINISTRATOR_ROLE,
                                        UserProfile.MANAGER_ROLE,
                                        UserProfile.PC_ROLE])

def user_can_access_user(logged_in_user, user):
    """
    Determines if the given logged-in user has permission to access
    another user's details.
    """
    if logged_in_user.pk == user.pk:
        return True

    profile = logged_in_user.get_profile()
    if profile.is_user():
        return False
    elif profile.is_admin():
        return True
    elif profile.is_manager():
        if models.access.managers_view_all_users:
            return True
        else:
            try:
                profile.managed_users.get(pk=user.pk)
                return True
            except User.DoesNotExist:
                return False
    elif profile.is_pc():
        try:
            profile.managed_users.get(pk=user.pk)
            return True
        except User.DoesNotExist:
            return False

def get_accessible_users(logged_in_user):
    """
    Returns a ``QuerySet`` of users accessible by the logged-in user. This
    will also include the logged-in user themselves.
    """
    profile = logged_in_user.get_profile()
    if profile.is_user():
        return User.objects.filter(pk=logged_in_user.pk)
    elif profile.is_admin():
        return User.objects.all()
    elif profile.is_manager():
        if models.access.managers_view_all_users:
            return User.objects.exclude(userprofile__role=UserProfile.ADMINISTRATOR_ROLE)
        else:
            return User.objects.filter(pk=logged_in_user.pk) | \
                profile.managed_users.all()
    elif profile.is_pc():
        return User.objects.filter(pk=logged_in_user.pk) | \
            profile.managed_users.all()

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
                from officeaid.views import permission_denied
                return permission_denied(request)
            return HttpResponseRedirect('%s?%s=%s' % (settings.LOGIN_URL, REDIRECT_FIELD_NAME, quote(request.get_full_path())))
        _checkuser.__doc__ = view_func.__doc__
        _checkuser.__dict__ = view_func.__dict__
        return _checkuser
    return _dec
