from django import newforms as forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import create_update, list_detail

from officeaid.forms.activities import ActivityFilterForm
from officeaid.models import Activity, Job
from officeaid.views import SortHeaders

LIST_HEADERS = (
    (u'Number',      'id'),
    (u'Job',         '%s.number' % Job._meta.db_table),
    (u'Created by',  None),
    (u'Created at',  'created_at'),
    (u'Priority',    'priority'),
    (u'Assigned to', None),
    (u'Contact',     None),
    (u'Description', None),
)

@login_required
def activity_list(request):
    """
    Lists Activities.

    A number of filter criteria may be applied to restrict Activities
    displayed based on a number of factors.
    """
    filter_form = ActivityFilterForm(request.GET)
    filters = filter_form.get_filters()
    sort_headers = SortHeaders(request, LIST_HEADERS,
                               additional_params=filter_form.get_params())
    if filters:
        queryset = Activity.objects.filter(**filters)
    else:
        queryset = Activity.objects.all()
    return list_detail.object_list(request,
        queryset.select_related().order_by(sort_headers.get_order_by()),
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='activity',
        template_name='activities/activity_list.html', extra_context={
            'filter_form': filter_form,
            'headers': list(sort_headers.headers()),
        })

@login_required
def add_activity(request):
    """
    Adds an Activity.

    Initial values for any Activity field may be specified as ``GET``
    parameters.
    """
    fields = ('job', 'description', 'priority', 'assigned_to', 'contact', 'due_date')
    ActivityForm = forms.form_for_model(Activity, fields=fields)
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.created_by = request.user
            activity.save()
            request.user.message_set.create(message=u'The %s was created sucessfully.' % Activity._meta.verbose_name)
            return HttpResponseRedirect(activity.get_absolute_url())
    else:
        # Fields may be pre-populated with query string parameters
        form = ActivityForm(initial=dict(request.GET.items()))
    return render_to_response('activities/add_activity.html', {
            'form': form,
        }, RequestContext(request))

@login_required
def activity_detail(request, activity_id):
    """
    Displays an Activity's details.
    """
    activity = get_object_or_404(Activity, pk=activity_id)
    return render_to_response('activities/activity_detail.html', {
            'activity': activity,
        }, RequestContext(request))

@login_required
def edit_activity(request, activity_id):
    """
    Edits an Activity.

    Only Activities which are not marked as completed may be edited.
    """
    activity = get_object_or_404(Activity, pk=activity_id)
    if activity.completed:
        return HttpResponseForbidden(u'Completed %s may not be edited.' \
                                     % Activity._meta.verbose_name_plural)
    fields = ('job', 'description', 'priority', 'assigned_to', 'contact',
              'due_date', 'completed')
    ActivityForm = forms.form_for_instance(activity, fields=fields)
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save()
            request.user.message_set.create(message=u'The %s was updated sucessfully.' % Activity._meta.verbose_name)
            return HttpResponseRedirect(activity.get_absolute_url())
    else:
        form = ActivityForm()
    return render_to_response('activities/edit_activity.html', {
            'activity': activity,
            'form': form,
        }, RequestContext(request))

@login_required
def delete_activity(request, activity_id):
    """
    Deletes an Activity.
    """
    activity = get_object_or_404(Activity, pk=activity_id)
    return create_update.delete_object(request, Activity,
        post_delete_redirect=reverse('activity_list'), object_id=activity_id,
        template_object_name='activity',
        template_name='activities/delete_activity.html')
