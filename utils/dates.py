import datetime
import time
from django.http import Http404

def is_week_commencing_date(date):
    """Does the given date represent the first day of the week?"""
    return date.isoweekday() == 1

def is_week_ending_date(date):
    """Does the given date represent the last day of the week?"""
    return date.isoweekday() == 7

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

def week_commencing_date(date):
    """
    Determines the week commencing date for the given date.

    That is, the first date on or before the given date which falls on
    the first day of the week.
    """
    if not is_week_commencing_date(date):
        return date - datetime.timedelta(days=date.isoweekday() - 1)
    return date

def week_ending_date(date):
    """
    Determines the week ending date for the given date.

    That is, the first date on or after the given date which falls on
    the last day of the week.
    """
    if not is_week_ending_date(date):
        return date + datetime.timedelta(days=7 - date.isoweekday())
    return date