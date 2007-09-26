from datetime import timedelta
from django import template
from django.core.urlresolvers import reverse
from django.utils import dateformat

register = template.Library()

##################
# Inclusion Tags #
##################

@register.inclusion_tag('timesheets/edit_time_entry_row.html', takes_context=True)
def edit_time_entry_row(context, entry, form):
    """
    Create content for a table row when editing the given Time Entry
    using the given Form.
    """
    return {
        'MEDIA_URL': context['MEDIA_URL'],
        'timesheet': context['timesheet'],
        'user_': context['user_'],
        'entry': entry,
        'form': form
    }

@register.inclusion_tag('timesheets/edit_expense_row.html', takes_context=True)
def edit_expense_row(context, expense, form):
    """
    Create content for a table row when editing the given Expense
    using the given Form.
    """
    return {
        'MEDIA_URL': context['MEDIA_URL'],
        'timesheet': context['timesheet'],
        'user_': context['user_'],
        'expense': expense,
        'form': form
    }

###########
# Filters #
###########

@register.filter
def add_time_entry_url(timesheet, user=None):
    """
    Looks up the URL for adding a Time Entry to the given Timesheet.
    """
    return reverse('add_time_entry', args=tuple(timesheet.url_parts(user)))

@register.filter
def add_expense_url(timesheet, user=None):
    """
    Looks up the URL for adding an Expense to the given Timesheet.
    """
    return reverse('add_expense', args=tuple(timesheet.url_parts(user)))

@register.filter
def approve_url(timesheet, user=None):
    """
    Looks up the URL for approving all items in the given Timesheet.
    """
    return reverse('approve_timesheet', args=tuple(timesheet.url_parts(user)))

@register.filter
def task_remaining(time_entry):
    """
    Displays the appropriate amount of time remaining on a Task.
    """
    if time_entry.task_remaining:
        return u'(%s)' % time_entry.task_remaining
    else:
        return max(0, time_entry.task_estimate_hours - time_entry.task_hours_booked)

#################
# Template Tags #
#################

@register.simple_tag
def day_headers(date):
    """
    Generate table headers for 7 days starting on the given date.
    """
    return u'\n'.join([u'<th scope="col">%s</th>' % \
                       dateformat.format(date + timedelta(days=i), r'D\<\b\r\>jS') \
                       for i in xrange(7)])
@register.simple_tag
def delete_time_entry_url(timesheet, user, id):
    """
    Looks up the URL for deleting the given Time Entry from the given
    Timesheet.
    """
    args = tuple(timesheet.url_parts(user) + [id])
    return reverse('delete_time_entry', args=args)


@register.simple_tag
def delete_expense_url(timesheet, user, id):
    """
    Looks up the URL for deleting the given Expense from the given
    Timesheet.
    """
    args = tuple(timesheet.url_parts(user) + [id])
    return reverse('delete_expense', args=args)
