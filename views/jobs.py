from django import newforms as forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.datastructures import DotExpandedDict
from django.views.generic import list_detail

from officeaid.auth import is_admin, is_admin_or_manager, user_has_permission
from officeaid.forms.jobs import AddJobForm, AddTaskForm, EditJobForm, JobFilterForm
from officeaid.models import Job, Task, TaskType
from officeaid.views import SortHeaders

LIST_HEADERS = (
    (u'Number', 'number'),
    (u'Name',   'name'),
    (u'Client', None),
    (u'Status', 'status'),
)

def filter_jobs(request):
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
    Lists Jobs, which are always filtered based on sytem settings and
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

@transaction.commit_on_success # Job creation is a multi-step process
@user_has_permission(is_admin_or_manager)
def add_job(request):
    """
    Adds a Job.

    This consists of defining a Job's details and, optionally, some
    Tasks.
    """
    clients = [(client.id, client.name) for client in Client.objects.all()]
    users = [(u.id, u.get_full_name()) \
             for u in User.objects.exclude(userprofile__role='A') \
                                   .order_by('first_name', 'last_name')]
    task_types = TaskType.objects.non_admin()

    if request.method == 'POST':
        # Job
        job_valid = False
        job_form = JobForm(clients, users, data=request.POST)
        if job_form.is_valid():
            job_valid = True

        # Tasks
        tasks_valid = True
        task_forms = []
        completed_task_forms = []
        for task_type in task_types:
            task_form = AddTaskForm(task_type, users, data=request.POST)
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
                task = Task.objects.create(job=job,
                    task_type=task_form.task_type,
                    estimate_hours=task_form.cleaned_data['estimate_hours'],
                    start_date=task_form.cleaned_data['start_date'],
                    end_date=task_form.cleaned_data['end_date'])
                task.assigned_users = task_form.cleaned_data['assigned_users']
            request.user.message_set.create(
                message=u'The %s was added successfully.' \
                        % Job._meta.verbose_name)
            return HttpResponseRedirect(job.get_absolute_url())
    else:
        job_form = JobForm(clients, users)
        task_forms = [AddTaskForm(task_type, users) for task_type in task_types]
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

@login_required
def edit_job(request, job_number):
    """
    Edits a Job.
    """
    job = get_object_or_404(Job, number=job_number)
    clients = [(client.id, client.name) for client in Client.objects.all()]
    users = [(u.id, u.get_full_name()) \
             for u in User.objects.exclude(userprofile__role='A') \
                                   .order_by('first_name', 'last_name')]

    if request.method == 'POST':
        # Job
        job_valid = False
        job_form = EditJobForm(job, clients, users, data=request.POST)
        if job_form.is_valid():
            job_valid = True

#        # Tasks
#        tasks_valid = True
#        task_count = 0
#        task_types = TaskType.objects.non_admin()
#        task_forms = []
#        completed_task_forms = []
#        for task_type in task_types:
#            task_form = AddTaskForm(task_type, users, data=request.POST)
#            task_forms.append(task_form)
#            if task_form.is_valid():
#                if task_form.cleaned_data['add']:
#                    completed_task_forms.append(task_form)
#                    task_count += 1
#            elif not tasks_valid:
#                tasks_valid = False
#        if task_count == 0:
#            tasks_valid = False
#
#        # If all data is valid, edit the Job and its Tasks, creating and
#        # deleting Tasks as necessary.
#        if job_valid and tasks_valid:
#            job = job_form.save()
#            for task_form in completed_task_forms:
#                task = Task.objects.create(job=job,
#                    task_type=task_form.task_type,
#                    estimate_hours=task_form.cleaned_data['estimate_hours'],
#                    start_date=task_form.cleaned_data['start_date'],
#                    end_date=task_form.cleaned_data['end_date'])
#                task.assigned_users = task_form.cleaned_data['assigned_users']
#            request.user.message_set.create(
#                message=u'The %s was added successfully.' \
#                        % Job._meta.verbose_name)
#            return HttpResponseRedirect(job.get_absolute_url())
    else:
        job_form = JobForm(job, clients, users)
#        task_forms = [AddTaskForm(task_type, users) \
#                      for task_type in TaskType.objects.non_admin()]
    return render_to_response('jobs/edit_job.html', {
            'job': job,
            'job_form': job_form,
#            'task_forms': task_forms,
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
