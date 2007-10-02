import string

from django import newforms as forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (HttpResponseBadRequest, HttpResponseForbidden,
    HttpResponseRedirect)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.views.generic import create_update, list_detail

from officeaid.models import Client, Contact, Job
from officeaid.views import SortHeaders
from officeaid.views.generic import add_object, edit_object

LIST_HEADERS = (
    (u'Name',         'last_name'),
    (u'Company Name', 'company_name'),
)

@login_required
def contact_list(request):
    """
    Lists Contacts.
    """
    sort_headers = SortHeaders(request, LIST_HEADERS)
    return list_detail.object_list(request,
        Contact.objects.order_by(sort_headers.get_order_by()),
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='contact',
        template_name='contacts/contact_list.html', extra_context={
            'headers': list(sort_headers.headers()),
        })

@login_required
def add_contact(request):
    """
    Adds a new Contact.
    """
    return add_object(request, Contact,
        template_name='contacts/add_contact.html')

@login_required
def contact_detail(request, contact_id):
    """
    Displays a Contact's details.
    """
    contact = get_object_or_404(Contact, pk=contact_id)
    return render_to_response('contacts/contact_detail.html', {
            'contact': contact,
            'activities': contact.activities.select_related(),
        }, RequestContext(request))

@login_required
def edit_contact(request, contact_id):
    """
    Edits a Contact.
    """
    return edit_object(request, Contact, contact_id,
        template_object_name='contact',
        template_name='contacts/edit_contact.html')

@login_required
def delete_contact(request, contact_id):
    """
    Deletes a Contact.
    """
    contact = get_object_or_404(Contact, pk=contact_id)
    if not contact.is_deleteable:
        return HttpResponseForbidden(u'The selected %s is not deleteable.' \
                                     % Contact._meta.verbose_name)
    return create_update.delete_object(request, Contact,
        post_delete_redirect=reverse('contact_list'), object_id=contact_id,
        template_object_name='contact',
        template_name='contacts/delete_contact.html')

@login_required
def assign_contacts(request, mode):
    """
    Assigns a Contact or Contacts from a pop-up window.
    """
    contacts = Contact.objects.all()

    if mode == 'multiple' and \
       request.GET.get('job_id', None) and \
       Job.objects.filter(pk=request.GET['job_id']).count():
        contacts = contacts.exclude(job_contact_jobs=request.GET['job_id'])
    elif request.GET.get('client_id', None) and \
       Client.objects.filter(pk=request.GET['client_id']).count():
        contacts = contacts.exclude(clients=request.GET['client_id'])

    contact_json = simplejson.dumps([dict(id=c.id, first_name=c.first_name,
        last_name=c.last_name, company_name=c.company_name,
        position=c.position) for c in contacts])
    return render_to_response('contacts/assign_contacts.html', {
            'mode': mode,
            'contact_json': contact_json,
            'letters': string.uppercase,
        }, RequestContext(request))
