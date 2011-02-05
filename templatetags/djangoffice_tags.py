from django import template

from djangoffice import auth

register = template.Library()

##################
# Inclusion Tags #
##################

@register.inclusion_tag('table_header.html')
def table_header(headers):
    """
    Creates a table header from the given header definitions.
    """
    return {'headers': headers}

@register.inclusion_tag('contacts/contact_rows.html')
def contact_rows(contact):
    """
    Creates table rows containing the given contact's details.
    """
    return {'contact': contact}

@register.inclusion_tag('jobs/filter_form.html', takes_context=True)
def job_filter_form(context, filter_form):
    """
    Displays a Job Filter Form.
    """
    return {
        'MEDIA_URL': context['MEDIA_URL'],
        'filter_form': filter_form,
    }

###########
# Filters #
###########

@register.filter
def pad_number(number):
    return u'%05d' % number

@register.filter
def is_admin_or_manager(user):
    return auth.is_admin_or_manager(user)