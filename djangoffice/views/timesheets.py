import datetime
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import pluralize
from django.utils import simplejson
from django.utils.safestring import mark_safe

from djangoffice.auth import (is_admin, is_admin_or_manager,
    user_can_access_user, user_has_permission)
from djangoffice.forms.timesheets import (BulkApprovalForm, AddTimeEntryForm,
    EditTimeEntryForm, ApprovedTimeEntryForm, AddExpenseForm, EditExpenseForm,
    ApprovedExpenseForm)
from djangoffice.models import (Expense, ExpenseType, Job, Task, TimeEntry,
    Timesheet)
from djangoffice.utils.dates import (is_week_commencing_date,
    week_commencing_date, week_ending_date)
from djangoffice.views import permission_denied

#####################
# Utility functions #
#####################

def week_commencing_date_or_404(year, month, day):
    """
    Converts date URL parameters to a date, raising ``Http404`` if the
    date is invalid or does not represent the first day of the week.
    """
    try:
        date = datetime.date(*time.strptime(year+month+day, '%Y%m%d')[:3])
        if not is_week_commencing_date(date):
            raise Http404
    except ValueError:
        raise Http404
    return date

def get_jobs_and_tasks_for_user(user):
    """
    Retrieves Job and Task information for the given user, returning
    them as a tuple.
    """
    tasks_by_job = {}
    for task in Task.objects.for_user_timesheet(user):
        if not tasks_by_job.has_key(task.job_id):
            tasks_by_job[task.job_id] = [task]
        else:
            tasks_by_job[task.job_id].append(task)
    jobs = [Job(**values) for values in \
            Job.objects.filter(id__in=tasks_by_job.keys()) \
             .order_by('number') \
              .values('id', 'name', 'number')]
    return (jobs, tasks_by_job)

def create_task_json(tasks_by_job):
    """
    Creates a JSON text representing an object mapping Job ids to Task
    ids and names.

    tasks_by_job
        A dict mapping Job ids to Tasks
    """
    json_dict = {}
    for job_id, tasks in tasks_by_job.iteritems():
        json_dict[job_id] = [dict(value=task.id, text=task.task_type_name) \
                             for task in tasks]
    return simplejson.dumps(json_dict)

#########
# Views #
#########

@login_required
def timesheet_index(request):
    """
    Redirects the logged-in User to their Timesheet for the current
    week.
    """
    week_commencing = week_commencing_date(datetime.date.today())
    timesheet, created = \
        Timesheet.objects.get_or_create(user=request.user,
                                        week_commencing=week_commencing)
    return HttpResponseRedirect(timesheet.get_absolute_url())

@transaction.commit_on_success
@user_has_permission(is_admin)
def bulk_approval(request):
    """
    Performs bulk approval of Time Entries and Expenses.
    """
    if request.method == 'POST':
        form = BulkApprovalForm(request.POST)
        if form.is_valid():
            start_date = week_commencing_date(form.cleaned_data['start_date'])
            end_date = week_ending_date(form.cleaned_data['end_date'])
            entries, expenses = Timesheet.objects.bulk_approve(request.user,
                                                               start_date,
                                                               end_date)
            return render_to_response('timesheets/bulk_approval.html', {
                'start_date': start_date,
                'end_date': end_date,
                'approved_time_entries': entries,
                'approved_expenses': expenses,
            }, RequestContext(request))
    else:
        form = BulkApprovalForm()
    return render_to_response('timesheets/bulk_approval.html', {
            'form': form,
        }, RequestContext(request))

@transaction.commit_on_success
@login_required
def edit_timesheet(request, username, year, month, day):
    """
    Edits a User's complete Timesheet for a particular week.
    """
    user = get_object_or_404(User, username=username)
    if not user_can_access_user(request.user, user):
        return permission_denied(request)
    week_commencing = week_commencing_date_or_404(year, month, day)
    timesheet, created = \
        Timesheet.objects.get_or_create(user=user,
                                        week_commencing=week_commencing)
    can_approve = is_admin_or_manager(request.user)
    jobs, tasks_by_job = get_jobs_and_tasks_for_user(user)
    expense_types = ExpenseType.objects.all()

    # Get Timesheet contents
    timesheet_time_entries = list(TimeEntry.objects.for_timesheet(timesheet))
    booked = TimeEntry.objects.hours_booked_for_tasks(
        [te.task_id for te in timesheet_time_entries])
    for time_entry in timesheet_time_entries:
        time_entry.task_hours_booked = booked[time_entry.task_id]
        time_entry.job_display = u'%05d - %s' % (time_entry.job_number,
                                                 time_entry.job_name)
    timesheet_expenses = list(Expense.objects.for_timesheet(timesheet))
    for expense in timesheet_expenses:
        expense.job_display = u'%05d - %s' % (expense.job_number,
                                              expense.job_name)

    # Create forms for timesheet contents, where necessary
    time_entries = []
    expenses = []

    if request.method == 'POST':
        # Create forms with POSTed data
        for time_entry in timesheet_time_entries:
            if time_entry.is_editable():
                time_entries.append((time_entry,
                    EditTimeEntryForm(time_entry, jobs,
                        tasks_by_job[time_entry.job_id], can_approve,
                        prefix='entry%s' % time_entry.id, data=request.POST)))
            elif time_entry.is_approved():
                time_entries.append((time_entry,
                    ApprovedTimeEntryForm(time_entry, can_approve,
                        prefix='entry%s' % time_entry.id, data=request.POST)))
            else:
                time_entries.append((time_entry, None))

        for expense in timesheet_expenses:
            if expense.is_editable():
                expenses.append((expense,
                    EditExpenseForm(expense, jobs, expense_types,
                        week_commencing, can_approve,
                        prefix='expense%s' % expense.id, data=request.POST)))
            elif expense.is_approved():
                expenses.append((expense,
                    ApprovedExpenseForm(expense, can_approve,
                        prefix='expense%s' % expense.id, data=request.POST)))
            else:
                expenses.append((expense, None))

        # Validate all forms
        all_valid = True
        for time_entry, form in time_entries:
            if form is not None and not form.is_valid():
                all_valid = False
                break

        for expense, form in expenses:
            if form is not None and not form.is_valid():
                all_valid = False
                break

        # Save if all forms are valid
        if all_valid:
            for time_entry, form in time_entries:
                if form:
                    form.save(request.user, commit=True)

            for expense, form in expenses:
                if form:
                    form.save(request.user, commit=True)

            messages.success(request, 'The %s was successfully saved.' \
                                       % Timesheet._meta.verbose_name)
            return HttpResponseRedirect(timesheet.get_absolute_url())
    else:
        # Create forms
        for time_entry in timesheet_time_entries:
            if time_entry.is_editable():
                time_entries.append((time_entry,
                    EditTimeEntryForm(time_entry, jobs,
                        tasks_by_job[time_entry.job_id], can_approve,
                        prefix='entry%s' % time_entry.id)))
            elif time_entry.is_approved():
                time_entries.append((time_entry,
                    ApprovedTimeEntryForm(time_entry, can_approve,
                        prefix='entry%s' % time_entry.id)))
            else:
                time_entries.append((time_entry, None))

        for expense in timesheet_expenses:
            if expense.is_editable():
                expenses.append((expense,
                    EditExpenseForm(expense, jobs, expense_types,
                        week_commencing, can_approve,
                        prefix='expense%s' % expense.id)))
            elif expense.is_approved():
                expenses.append((expense,
                    ApprovedExpenseForm(expense, can_approve,
                        prefix='expense%s' % expense.id)))
            else:
                expenses.append((expense, None))

    return render_to_response('timesheets/edit_timesheet.html', {
            'user_': user,
            'timesheet': timesheet,
            'time_entries': time_entries,
            'expenses': expenses,
            'task_json': mark_safe(create_task_json(tasks_by_job)),
            'can_approve': can_approve,
        }, RequestContext(request))

@transaction.commit_on_success
@user_has_permission(is_admin_or_manager)
def approve_timesheet(request, username, year, month, day):
    """
    Approves all Time Entries and Expenses in a User's Timesheet for a
    particular week.
    """
    if request.method != 'POST':
        raise Http404
    user = get_object_or_404(User, username=username)
    if not user_can_access_user(request.user, user):
        return permission_denied(request)
    week_commencing = week_commencing_date_or_404(year, month, day)
    timesheet, created = \
        Timesheet.objects.get_or_create(user=user,
                                        week_commencing=week_commencing)
    entries, expenses = timesheet.approve(request.user)
    messages.success(requset, '%s time entr%s and %s expense%s were approved.' \
                              % (entries, pluralize(entries, u'y,ies'),
                                 expenses, pluralize(expenses)))
    return HttpResponseRedirect(timsheet.get_absolute_url())

@transaction.commit_on_success
@login_required
def prepopulate_timesheet(request, username, year, month, day):
    """
    Prepopulates a Timesheet with empty Time Entries for the Tasks the
    User booked Time Entries against in the previous week's Timesheet.
    """
    user = get_object_or_404(User, username=username)
    if not user_can_access_user(request.user, user):
        return permission_denied(request)
    week_commencing = week_commencing_date_or_404(year, month, day)
    timesheet, created = \
        Timesheet.objects.get_or_create(user=user,
                                        week_commencing=week_commencing)
    try:
        previous_week_commencing = week_commencing - datetime.timedelta(days=7)
        previous_timesheet = \
            Timesheet.objects.get(user=user,
                                  week_commencing=previous_week_commencing)
        task_types = TaskType.objects \
                      .filter(tasks__timeentries__timesheet=previous_timesheet) \
                       .distinct()
        for task_type in task_types:
            TimeEntry.objects.create(timesheet=timesheet, task_type=task_type)
        messages.success(request,
                         "Successfully prepopulated Time Entries from the previous week's Timesheet.")
    except Timesheet.DoesNotExist:
        messages.warning('Cannot prepopulate as there is no Timesheet for the previous week.')
    return HttpResponseRedirect(timesheet.get_absolute_url())

@transaction.commit_on_success
@login_required
def add_time_entry(request, username, year, month, day):
    """
    Adds a Time Entry to a User's Timesheet.
    """
    user = get_object_or_404(User, username=username)
    if user.get_profile().is_admin():
        return HttpResponseBadRequest(
            u'Time Entries may not be created for administration accounts.')
    if not user_can_access_user(request.user, user):
        return permission_denied(request)
    jobs, tasks_by_job = get_jobs_and_tasks_for_user(user)
    week_commencing = week_commencing_date_or_404(year, month, day)
    timesheet, created = \
        Timesheet.objects.get_or_create(user=user,
                                        week_commencing=week_commencing)

    if request.method == 'POST':
        try:
            form_tasks = tasks_by_job[int(request.POST['job'])]
        except:
            form_tasks = None
        form = AddTimeEntryForm(jobs, tasks=form_tasks, data=request.POST)
        if form.is_valid():
            entry = form.save(timesheet=timesheet)
            messages.success(request, 'The %s was added successfully' \
                                      % TimeEntry._meta.verbose_name)
            return HttpResponseRedirect(reverse('edit_timesheet',
                                                args=(username, year, month,
                                                      day)))
    else:
        form = AddTimeEntryForm(jobs)
    return render_to_response('timesheets/add_time_entry.html', {
            'user_': user,
            'timesheet': timesheet,
            'form': form,
            'task_json': mark_safe(create_task_json(tasks_by_job)),
        }, RequestContext(request))

@transaction.commit_on_success
@login_required
def delete_time_entry(request, username, year, month, day, time_entry_id):
    """
    Deletes a Time Entry from a User's Timesheet.
    """
    user = get_object_or_404(User, username=username)
    if not user_can_access_user(request.user, user):
        return permission_denied(request)
    week_commencing = week_commencing_date_or_404(year, month, day)
    timesheet = get_object_or_404(Timesheet, user=user,
                                  week_commencing=week_commencing)
    time_entry = get_object_or_404(TimeEntry.objects.for_timesheet(timesheet),
                                   pk=time_entry_id)
    if not time_entry.is_editable():
        return HttpResponseForbidden(u'The selected %s is not deleteable.' \
                                     % TimeEntry._meta.verbose_name)

    if request.method == 'POST':
        time_entry.delete()
        messages.success(request, 'The %s was deleted successfully.' \
                                  % TimeEntry._meta.verbose_name)
        return HttpResponseRedirect(timesheet.get_absolute_url())
    else:
        time_entry.job_display = u'%05d - %s' % (time_entry.job_number,
                                                 time_entry.job_name)
        return render_to_response('timesheets/delete_time_entry.html', {
                'user_': user,
                'timesheet': timesheet,
                'entry': time_entry,
            }, RequestContext(request))

@transaction.commit_on_success
@login_required
def add_expense(request, username, year, month, day):
    """
    Adds an Expense to a User's Timesheet.
    """
    user = get_object_or_404(User, username=username)
    if not user_can_access_user(request.user, user):
        return permission_denied(request)
    jobs, tasks_by_job = get_jobs_and_tasks_for_user(user)
    week_commencing = week_commencing_date_or_404(year, month, day)
    timesheet, created = \
        Timesheet.objects.get_or_create(user=user,
                                        week_commencing=week_commencing)

    if request.method == 'POST':
        form = AddExpenseForm(jobs, week_commencing, data=request.POST)
        if form.is_valid():
            expense = form.save(timesheet=timesheet)
            messages.success(request, 'The %s was added successfully' \
                                      % Expense._meta.verbose_name)
            return HttpResponseRedirect(reverse('edit_timesheet',
                                                args=(username, year, month,
                                                      day)))
    else:
        form = AddExpenseForm(jobs, week_commencing)
    return render_to_response('timesheets/add_expense.html', {
            'user_': user,
            'timesheet': timesheet,
            'form': form,
        }, RequestContext(request))

@transaction.commit_on_success
@login_required
def delete_expense(request, username, year, month, day, expense_id):
    """
    Deletes an Expense from a User's Timesheet.
    """
    user = get_object_or_404(User, username=username)
    if not user_can_access_user(request.user, user):
        return permission_denied(request)
    week_commencing = week_commencing_date_or_404(year, month, day)
    timesheet = get_object_or_404(Timesheet, user=user,
                                  week_commencing=week_commencing)
    expense = get_object_or_404(Expense.objects.for_timesheet(timesheet),
                                pk=expense_id)
    if not expense.is_editable():
        return HttpResponseForbidden(u'The selected %s is not deleteable.' \
                                     % Expense._meta.verbose_name)

    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'The %s was deleted successfully.' \
                                  % Expense._meta.verbose_name)
        return HttpResponseRedirect(timesheet.get_absolute_url())
    else:
        expense.job_display = u'%05d - %s' % (expense.job_number,
                                              expense.job_name)
        return render_to_response('timesheets/delete_expense.html', {
                'user_': user,
                'timesheet': timesheet,
                'expense': expense,
            }, RequestContext(request))
