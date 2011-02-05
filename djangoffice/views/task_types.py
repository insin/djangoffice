from django import newforms as forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import create_update, list_detail

from djangoffice.auth import is_admin_or_manager, user_has_permission
from djangoffice.forms.rates import EditRateForm, TaskTypeRateBaseForm
from djangoffice.models import TaskType, TaskTypeRate
from djangoffice.views import SortHeaders
from djangoffice.views.generic import add_object, edit_object

LIST_HEADERS = (
    (u'Task Type', 'name'),
)

@user_has_permission(is_admin_or_manager)
def task_type_list(request):
    """
    Lists Task Types.
    """
    sort_headers = SortHeaders(request, LIST_HEADERS)
    return list_detail.object_list(request,
        TaskType.objects.non_admin().order_by(sort_headers.get_order_by()),
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='task_type',
        template_name='task_types/task_type_list.html', extra_context={
            'headers': list(sort_headers.headers()),
        })

@user_has_permission(is_admin_or_manager)
def add_task_type(request):
    """
    Adds a new Task Type.
    """
    return add_object(request, TaskType,
        template_name='task_types/add_task_type.html')

@user_has_permission(is_admin_or_manager)
def task_type_detail(request, task_type_id):
    """
    Displays a Task Type's details.
    """
    task_type = get_object_or_404(TaskType, pk=task_type_id)
    return render_to_response('task_types/task_type_detail.html', {
            'task_type': task_type,
            'rates': task_type.rates.order_by('effective_from'),
        }, RequestContext(request))

@user_has_permission(is_admin_or_manager)
def edit_task_type(request, task_type_id):
    """
    Edits a Task Type.
    """
    return edit_object(request, TaskType, task_type_id,
        template_object_name = 'task_type',
        template_name='task_types/edit_task_type.html')

@transaction.commit_on_success
@user_has_permission(is_admin_or_manager)
def edit_task_type_rates(request, task_type_id):
    """
    Edits a Task Type's Rates.
    """
    task_type = get_object_or_404(TaskType, pk=task_type_id)
    rates = []
    editable_rates = False
    if request.method == 'POST':
        for rate in task_type.rates.order_by('effective_from'):
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
                                % TaskTypeRate._meta.verbose_name_plural)
                    return HttpResponseRedirect(task_type.get_absolute_url())
    else:
        for rate in task_type.rates.order_by('effective_from'):
            if rate.editable:
                rates.append((rate, EditRateForm(rate,
                                                 prefix='rate%s' % rate.id)))
                if not editable_rates:
                    editable_rates = True
            else:
                rates.append((rate, None))
    return render_to_response('task_types/edit_task_type_rates.html', {
            'task_type': task_type,
            'rates': rates,
            'editable_rates': editable_rates,
        }, RequestContext(request))

@user_has_permission(is_admin_or_manager)
def add_task_type_rate(request, task_type_id):
    """
    Adds a new Task Type Rate.
    """
    task_type = get_object_or_404(TaskType, pk=task_type_id)
    TaskTypeRateForm = forms.form_for_model(TaskTypeRate,
        form=TaskTypeRateBaseForm, fields=('effective_from', 'standard_rate',
                                           'overtime_rate'))
    if request.method == 'POST':
        form = TaskTypeRateForm(task_type, request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.task_type = task_type
            rate.editable = True
            rate.save()
            request.user.message_set.create(
                message=u'The %s was added successfully.' \
                        % TaskTypeRate._meta.verbose_name)
            return HttpResponseRedirect(reverse('edit_task_type_rates',
                                                args=(task_type.id,)))
    else:
        form = TaskTypeRateForm(task_type)
    return render_to_response('task_types/add_task_type_rate.html', {
            'form': form,
            'task_type': task_type,
            'rates': task_type.rates.order_by('effective_from'),
        }, RequestContext(request))

@user_has_permission(is_admin_or_manager)
def delete_task_type(request, task_type_id):
    """
    Deletes a Task Type.
    """
    task_type = get_object_or_404(TaskType, pk=task_type_id)
    if not task_type.is_deleteable:
        return HttpResponseForbidden(u'The selected %s is not deleteable.' \
                                     % TaskType._meta.verbose_name)
    return create_update.delete_object(request, TaskType,
        post_delete_redirect=reverse('task_type_list'),
        object_id=task_type_id, template_object_name='task_type',
        template_name='task_types/delete_task_type.html')
