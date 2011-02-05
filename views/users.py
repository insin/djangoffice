from django import newforms as forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.core.urlresolvers import reverse
from django.db import backend, connection, transaction
from django.db.models import Q
from django.db.models.query import find_field
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import create_update, list_detail

from djangoffice import models
from djangoffice.auth import is_admin, is_admin_or_manager, user_has_permission
from djangoffice.forms.rates import EditRateForm, UserRateBaseForm
from djangoffice.forms.users import AdminUserForm, EditUserForm, UserForm
from djangoffice.models import Job, Task, UserRate, UserProfile
from djangoffice.views import SortHeaders

#####################
# Utility functions #
#####################

def assign_user_to_admin_job_tasks(user):
    """
    Assigns the given User to all Admin Job Tasks.
    """
    admin_job = Job.objects.get(id=settings.ADMIN_JOB_ID)
    task_ids = [task.id for task in admin_job.tasks.all()]
    db_table = find_field('assigned_users',
                          Task._meta.many_to_many, False).m2m_db_table()
    query = 'INSERT INTO %s (%s,%s) VALUES %s' % (
        backend.quote_name(db_table),
        backend.quote_name('task_id'),
        backend.quote_name('user_id'),
        ','.join(['(%s,%s)'] * len(task_ids)),
    )
    params = []
    for task_id in task_ids:
        params.append(task_id)
        params.append(user.id)
    cursor = connection.cursor()
    cursor.execute(query, params)

def users_accessible_to_user(user):
    """
    Creates a ``QuerySet`` containing Users the given User has access
    to.

    Admins may access all Users, as may Managers when the appropriate
    access setting is enabled.

    Otherwise, Managers may only see themselves and their managed Users;
    Users may only see themselves.
    """
    profile = user.get_profile()
    if (profile.is_admin()
        or (profile.is_manager() and models.access.managers_view_all_users)):
        return User.objects.exclude(userprofile__role=UserProfile.ADMINISTRATOR_ROLE)
    elif profile.is_manager():
        return User.objects.filter(Q(pk=user.id) | Q(managers=user.id))
    elif profile.is_user():
        return User.objects.filter(pk=user.id)

#########
# Views #
#########

def login(request):
    """
    Logs a user in - a simple wrapper around the contrib login view.
    """
    return auth_views.login(request, template_name='users/login.html')

def logout(request):
    """
    Logs a user out - a simple wrapper around the contrib logout view.
    """
    return auth_views.logout(request, template_name='users/logged_out.html')

LIST_HEADERS = (
    (u'User Name', 'username'),
    (u'Role',      'auth_user__userprofile.role'),
    (u'Forename',  'first_name'),
    (u'Surname',   'last_name'),
    (u'Email',     None),
    (u'Login',     None),
)

@login_required
def user_list(request):
    """
    Lists Users.
    """
    admin = User.objects.get(userprofile__role=UserProfile.ADMINISTRATOR_ROLE)
    sort_headers = SortHeaders(request, LIST_HEADERS)
    users = users_accessible_to_user(request.user) \
             .select_related() \
              .order_by(sort_headers.get_order_by())
    return list_detail.object_list(request, users,
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='user', template_name='users/user_list.html',
        extra_context={
            'admin': admin,
            'headers': list(sort_headers.headers()),
        })

@transaction.commit_on_success
@user_has_permission(is_admin_or_manager)
def add_user(request):
    """
    Adds a new User.
    """
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(form.cleaned_data['username'],
                form.cleaned_data['email'], form.cleaned_data['password'])
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            # Create profile
            profile = UserProfile.objects.create(user=user,
                role=form.cleaned_data['role'],
                phone_number=form.cleaned_data['phone_number'],
                mobile_number=form.cleaned_data['mobile_number'])
            if profile.role in [UserProfile.MANAGER_ROLE, UserProfile.PM_ROLE] and \
               form.cleaned_data['managed_users']:
                profile.managed_users = form.cleaned_data['managed_users']

            # Assign the user to all Admin job tasks
            assign_user_to_admin_job_tasks(user)

            request.user.message_set.create(
                message=u'The %s was added successfully.' \
                        % User._meta.verbose_name)
            return HttpResponseRedirect(user.get_absolute_url())
    else:
        form = UserForm()
    return render_to_response('users/add_user.html', {
            'form': form,
        }, RequestContext(request))

@login_required
def user_detail(request, username):
    """
    Displays a User's details.
    """
    user = get_object_or_404(User, username=username)
    return render_to_response('users/user_detail.html', {
            'user_': user,
            'profile': user.get_profile(),
            'rates': user.rates.order_by('effective_from'),
            'activities': user.assigned_activities.all(),
        }, RequestContext(request))

@transaction.commit_on_success
@user_has_permission(is_admin_or_manager)
def edit_user(request, username):
    """
    Edits a User - only Users with 'Manager' or 'User' roles may be
    edited using this view.
    """
    user = get_object_or_404(User, username=username)
    profile = user.get_profile()
    if profile.is_admin():
        return HttpResponseForbidden(
            u'The specified User is not editable at this location.')
    if request.method == 'POST':
        form = EditUserForm(request.POST)
        if form.is_valid():
            # Update user
            for attr in ('first_name', 'last_name', 'email'):
                setattr(user, attr, form.cleaned_data[attr])
            user.is_active = not form.cleaned_data['disabled']
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
            user.save()

            # Update profile
            for attr in ('role', 'phone_number', 'mobile_number'):
                setattr(profile, attr, form.cleaned_data[attr])
            # Update managed users, clearing them when neccessary
            manage_users_roles = [UserProfile.MANAGER_ROLE, UserProfile.PM_ROLE]
            if profile.role in manage_users_roles and \
               form.cleaned_data['role'] not in manage_users_roles:
                # Not a manager any more
                profile.managed_users.clear()
            elif form.cleaned_data['role'] in manage_users_roles:
                if not form.cleaned_data['managed_users']:
                    profile.managed_users.clear()
                else:
                    profile.managed_users = form.cleaned_data['managed_users']
            profile.save()

            request.user.message_set.create(
                message=u'The %s was edited successfully.' \
                        % User._meta.verbose_name)
            return HttpResponseRedirect(user.get_absolute_url())
    else:
        initial = {
            'role': profile.role,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': profile.phone_number,
            'mobile_number': profile.mobile_number,
            'disabled': not user.is_active,
            'managed_users': [u.id for u in profile.managed_users.all()],
        }
        form = EditUserForm(initial=initial)
    return render_to_response('users/edit_user.html', {
            'form': form,
            'user_': user,
            'profile': profile,
        }, RequestContext(request))

@transaction.commit_on_success
@user_has_permission(is_admin_or_manager)
def edit_user_rates(request, username):
    """
    Edits a User's Rates.
    """
    user = get_object_or_404(User, username=username)
    rates = []
    editable_rates = False
    if request.method == 'POST':
        for rate in user.rates.order_by('effective_from'):
            if rate.editable:
                rates.append((rate, EditRateForm(rate,
                                                 prefix='rate%s' % rate.id,
                                                 data=request.POST)))
                if not editable_rates:
                    editable_rates = True
            else:
                rates.append((rate, None))

        all_valid = True
        for rate, form in rates:
            if form is not None:
                if not form.is_valid():
                    all_valid = False
                    break

        if all_valid:
            for rate, form in rates:
                if form is not None:
                    rate.standard_rate = form.cleaned_data['standard_rate']
                    rate.overtime_rate = form.cleaned_data['overtime_rate']
                    rate.save()
                    request.user.message_set.create(
                        message=u'%s were edited successfully.' \
                                % UserRate._meta.verbose_name_plural)
                    return HttpResponseRedirect(user.get_absolute_url())
    else:
        for rate in user.rates.order_by('effective_from'):
            if rate.editable:
                rates.append((rate, EditRateForm(rate,
                                                 prefix='rate%s' % rate.id)))
                if not editable_rates:
                    editable_rates = True
            else:
                rates.append((rate, None))
    return render_to_response('users/edit_user_rates.html', {
            'user_': user,
            'rates': rates,
            'editable_rates': editable_rates,
        }, RequestContext(request))

@user_has_permission(is_admin_or_manager)
def add_user_rate(request, username):
    """
    Adds a new User Rate.
    """
    user = get_object_or_404(User, username=username)
    UserRateForm = forms.form_for_model(UserRate,
        form=UserRateBaseForm, fields=('effective_from', 'standard_rate',
                                       'overtime_rate'))
    if request.method == 'POST':
        form = UserRateForm(user, request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.user = user
            rate.editable = True
            rate.save()
            request.user.message_set.create(
                message=u'The %s was added successfully.' \
                        % UserRate._meta.verbose_name)
            return HttpResponseRedirect(reverse('edit_user_rates',
                                                args=(username,)))
    else:
        form = UserRateForm(user)
    return render_to_response('users/add_user_rate.html', {
            'form': form,
            'user_': user,
            'rates': user.rates.order_by('effective_from'),
        }, RequestContext(request))

@user_has_permission(is_admin)
def edit_admin_user(request):
    """
    Edits the User who has the 'Administrator' role. This user will
    only have a small subset of their details editable.
    """
    editable_attrs = ['username', 'first_name', 'last_name', 'email']
    admin = User.objects.get(userprofile__role=UserProfile.ADMINISTRATOR_ROLE)
    if request.method == 'POST':
        form = AdminUserForm(request.POST)
        if form.is_valid():
            for attr in editable_attrs:
                setattr(admin, attr, form.cleaned_data[attr])
            if form.cleaned_data['password'] is not None:
                admin.set_password(form.cleaned_data['password'])
            admin.save()
            request.user.message_set.create(
                message=u'The %s was edited successfully.' \
                        % User._meta.verbose_name)
            return HttpResponseRedirect(reverse('user_list'))
    else:
        initial = dict([(attr, getattr(admin, attr)) \
                        for attr in editable_attrs])
        form = AdminUserForm(initial=initial)
    return render_to_response('users/edit_admin_user.html', {
            'admin': admin,
            'form': form,
        }, RequestContext(request))

@user_has_permission(is_admin_or_manager)
def delete_user(request, username):
    """
    Deletes a User.
    """
    user = get_object_or_404(User, username=username)
    profile = user.get_profile()
    if profile.is_admin():
        return HttpResponseForbidden(u'The specified User is not deleteable.')
    return create_update.delete_object(request, User,
        post_delete_redirect=reverse('user_list'), object_id=user.id,
        template_object_name='user_',
        template_name='users/delete_user.html')
