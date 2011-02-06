from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import create_update, list_detail

from djangoffice.auth import is_admin_or_manager, user_has_permission
from djangoffice.models import ActivityType
from djangoffice.views import SortHeaders
from djangoffice.views.generic import add_object, edit_object

LIST_HEADERS = (
    (u'Name',        'name'),
    (u'Access',      'access'),
    (u'Description', None),
)

@user_has_permission(is_admin_or_manager)
def activity_type_list(request):
    """
    Lists Activity Types.
    """
    sort_headers = SortHeaders(request, LIST_HEADERS)
    return list_detail.object_list(request,
        ActivityType.objects.order_by(sort_headers.get_order_by()),
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='activity_type',
        template_name='activity_types/activity_type_list.html', extra_context={
            'headers': list(sort_headers.headers()),
        })

@user_has_permission(is_admin_or_manager)
def add_activity_type(request):
    """
    Adds an Activity Type.
    """
    return add_object(request, ActivityType,
        template_name='activity_types/add_activity_type.html')

@user_has_permission(is_admin_or_manager)
def activity_type_detail(request, activity_type_id):
    """
    Displays an Activity Type's details.
    """
    activity_type = get_object_or_404(ActivityType, pk=activity_type_id)
    return render_to_response('activity_types/activity_type_detail.html', {
            'activity_type': activity_type,
        }, RequestContext(request))

@user_has_permission(is_admin_or_manager)
def edit_activity_type(request, activity_type_id):
    """
    Edits an Activity Type.
    """
    return edit_object(request, ActivityType, activity_type_id,
        template_object_name = 'activity_type',
        template_name='activity_types/edit_activity_type.html')

@user_has_permission(is_admin_or_manager)
def delete_activity_type(request, activity_type_id):
    """
    Deletes an Activity Type.
    """
    activity_type = get_object_or_404(ActivityType, pk=activity_type_id)
    if not activity_type.is_deleteable:
        return HttpResponseForbidden(u'The selected %s is not deleteable.' \
                                     % ActivityType._meta.verbose_name)
    return create_update.delete_object(request, ActivityType,
        post_delete_redirect=reverse('activity_type_list'),
        object_id=activity_type_id,
        template_object_name='activity_type',
        template_name='activity_types/delete_activity_type.html')
