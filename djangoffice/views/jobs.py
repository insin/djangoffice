from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import list_detail

from djangoffice.auth import is_admin, is_admin_or_manager, user_has_permission
from djangoffice.forms.jobs import (AddJobForm, AddTaskForm, EditJobForm,
    EditTaskForm, JobFilterForm)
from djangoffice.models import Job, Task, TaskType, UserProfile
from djangoffice.views import SortHeaders

LIST_HEADERS = (
    (u'Number', 'number'),
    (u'Name',   'name'),
    (u'Client', None),
    (u'Status', 'status'),
)

def filter_jobs(request):
    """
    Handles filtering Jobss by search criteria, sorting, pagination and
    restriction of Jobs to those accessible by the logged-in User.
    """
    filter_form = JobFilterForm(data=request.GET)
    sort_headers = SortHeaders(request, LIST_HEADERS,
                               additional_params=filter_form.get_params())
    jobs = Job.objects.accessible_to_user(request.user) \
                       .order_by(sort_headers.get_order_by())

    # Apply filters if any were specified
    filters = filter_form.get_filters()
    if filters is not None:
        jobs = jobs & Job.objects.filter(filters)
        if filter_form.make_distinct:
            jobs = jobs.distinct()

    return jobs, filter_form, sort_headers

@login_required
def job_list(request):
    """
    Lists Jobs, which are always filtered based on system settings and
    the logged-in User's role.

    Jobs listed may be further filtered based on a number of criteria.
    """
    jobs, filter_form, sort_headers = filter_jobs(request)
    return list_detail.object_list(request, jobs,
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='job', template_name='jobs/job_list.html',
        extra_context={
            'filter_form': filter_form,
            'headers': list(sort_headers.headers()),
        })

@transaction.commit_on_success
@user_has_permission(is_admin_or_manager)
def add_job(request):
    """
    Adds a Job.

    This consists of defining a Job's details and, optionally, some
    Tasks.
    """
    users = list(User.objects.exclude(userprofile__role=UserProfile.ADMINISTRATOR_ROLE) \
                              .order_by('first_name', 'last_name'))
    user_choices = [(u.pk, u.get_full_name()) for u in users]
    task_types = TaskType.objects.non_admin()

    if request.method == 'POST':
        # Job
        job_valid = False
        job_form = AddJobForm(users, data=request.POST)
        if job_form.is_valid():
            job_valid = True

        # Tasks
        tasks_valid = True
        task_forms = []
        completed_task_forms = []
        for task_type in task_types:
            task_form = AddTaskForm(task_type, user_choices, data=request.POST)
            task_forms.append(task_form)
            if task_form.is_valid():
                if task_form.cleaned_data['add']:
                    completed_task_forms.append(task_form)
            elif not tasks_valid:
                tasks_valid = False
        if len(completed_task_forms) == 0:
            tasks_valid = False

        # If all data is valid, create the Job and its Tasks
        if job_valid and tasks_valid:
            job = job_form.save()
            for task_form in completed_task_forms:
                task_form.save(job)
            messages.success(request, 'The %s was added successfully.' \
                                      % Job._meta.verbose_name)
            return HttpResponseRedirect(job.get_absolute_url())
    else:
        job_form = AddJobForm(users)
        task_forms = [AddTaskForm(task_type, user_choices) \
                      for task_type in task_types]
    return render_to_response('jobs/add_job.html', {
            'job_form': job_form,
            'task_forms': task_forms,
        }, RequestContext(request))

@login_required
def job_detail(request, job_number):
    """
    Displays a Job's details.
    """
    try:
        job = Job.objects.select_related().get(number=job_number)
    except Job.DoesNotExist:
        raise Http404(u'No %s matches the given query.' \
                      % Job._meta.verbose_name)
    return render_to_response('jobs/job_detail.html', {
            'job': job,
            'job_contacts': job.job_contacts.all(),
            'activities': job.activities.all(),
            'tasks': job.tasks.all(),
            'invoices': job.invoices.all(),
            'artifacts': job.artifacts.all(),
        }, RequestContext(request))

@transaction.commit_on_success
@login_required
def edit_job(request, job_number):
    """
    Edits a Job and its Tasks.

    New Tasks may also be added for Task Types which are not yet assigned
    Tasks for the Job.
    """
    job = get_object_or_404(Job, number=job_number)
    users = list(User.objects.exclude(userprofile__role=UserProfile.ADMINISTRATOR_ROLE) \
                              .order_by('first_name', 'last_name'))
    user_choices = [(u.pk, u.get_full_name()) for u in users]
    tasks = Task.objects.with_task_type_name().filter(job=job)
    task_types = TaskType.objects.exclude_by_job(job.pk)

    if request.method == 'POST':
        job_form = EditJobForm(job, users, data=request.POST)

        # Existing Tasks
        tasks_valid = True
        task_forms = []
        for task in tasks:
            task_form = EditTaskForm(task, user_choices, data=request.POST)
            task_forms.append(task_form)
            if not task_form.is_valid() and tasks_valid:
                tasks_valid = False

        # New Tasks
        new_tasks_valid = True
        new_task_forms = []
        completed_new_task_forms = []
        for task_type in task_types:
            task_form = AddTaskForm(task_type, user_choices, data=request.POST)
            new_task_forms.append(task_form)
            if task_form.is_valid():
                if task_form.cleaned_data['add']:
                    completed_new_task_forms.append(task_form)
            elif not new_tasks_valid:
                new_tasks_valid = False

        # If all data is valid, edit the Job and its Tasks, creating any
        # new Tasks if necessary.
        if job_form.is_valid() and tasks_valid and new_tasks_valid:
            job = job_form.save()
            for task_form in task_forms:
                task_form.save()
            for task_form in completed_new_task_forms:
                task_form.save(job)
            messages.success(request, 'The %s was edited successfully.' \
                                      % Job._meta.verbose_name)
            return HttpResponseRedirect(job.get_absolute_url())
    else:
        job_form = EditJobForm(job, users)
        task_forms = [EditTaskForm(task, user_choices) for task in tasks]
        new_task_forms = [AddTaskForm(task_type, user_choices) \
                          for task_type in task_types]
    return render_to_response('jobs/edit_job.html', {
            'job': job,
            'job_form': job_form,
            'task_forms': task_forms,
            'new_task_forms': new_task_forms,
        }, RequestContext(request))

@user_has_permission(is_admin_or_manager)
def delete_job(request, job_number):
    """
    Deletes a Job.
    """
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def preview_job_quote(request, job_number):
    """
    Previews a Job's quote PDF.
    """
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def generate_job_quote(request, job_number):
    """
    Generates a Job's quote PDF, storing it as an Artifact.
    """
    raise NotImplementedError
