import datetime

from django.core.exceptions import ValidationError

from djangoffice.utils.dates import is_week_commencing_date

def isWeekCommencingDate(value):
    """
    Validates that a date falls on the first day of the week.
    """
    if not is_week_commencing_date(value):
        raise ValidationError('Enter a date which falls on the first day of the week.')

def isSafeishQuery(value):
    """
    Naively validates that a field does not contain any potentially
    destructive SQL.
    """
    value = value.upper()
    for keyword in ['INSERT', 'UPDATE', 'DELETE']:
        if keyword in value:
            raise ValidationError('Queries may not contain INSERT, UPDATE or DELETE.')
