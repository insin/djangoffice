import datetime

from django.core.validators import ValidationError

from djangoffice.utils.dates import is_week_commencing_date

class OnlyAllowedIfOtherFieldEquals(object):
    """
    Validates that a value may only be given for a field when another
    field has a specific value.

    >>> v = OnlyAllowedIfOtherFieldEquals('other_field', 'OK')
    >>> v('Something', {'other_field': 'OK'})
    >>> v('Something', {'other_field': 'Not OK'})
    Traceback (most recent call last):
        ...
    ValidationError: [u'This field must only be given if other_field is OK.']
    >>> v = OnlyAllowedIfOtherFieldEquals('other_field', 'OK', 'TODO Define error message.')
    >>> v('Something', {'other_field': 'OK'})
    >>> v('Something', {'other_field': 'Not OK'})
    Traceback (most recent call last):
        ...
    ValidationError: [u'TODO Define error message.']
    """
    def __init__(self, other_field, other_value, error_message=None):
        self.other_field = other_field
        self.other_value = other_value
        self.error_message = error_message or \
            u'This field must only be given if %(field)s is %(value)s.' % {
                'field': other_field, 'value': other_value}
        self.always_test = True

    def __call__(self, field_data, all_data):
        if all_data.has_key(self.other_field) and not \
           all_data[self.other_field] == self.other_value and field_data:
            raise ValidationError(self.error_message)

def isWeekCommencingDate(field_data, all_data):
    """
    Validates that a date falls on the first day of the week.

    >>> isWeekCommencingDate('2007-10-29', {})
    >>> isWeekCommencingDate('2007-10-30', {})
    Traceback (most recent call last):
        ...
    ValidationError: [u'Enter a date which falls on the first day of the week.']
    """
    year, month, day = map(int, field_data.split('-'))
    if not is_week_commencing_date(datetime.date(year, month, day)):
        raise ValidationError(
            u'Enter a date which falls on the first day of the week.')

def isSafeishQuery(field_data, all_data):
    """
    Naively validates that a field does not contain any potentially
    destructive SQL.

    >>> isSafeishQuery('SELECT * FROM some_table', {})
    >>> isSafeishQuery('DELETE FROM some_table', {})
    Traceback (most recent call last):
        ...
    ValidationError: [u'Queries may not contain INSERT, UPDATE or DELETE.']
    >>> isSafeishQuery('UPDATE some_table SET something = NULL', {})
    Traceback (most recent call last):
        ...
    ValidationError: [u'Queries may not contain INSERT, UPDATE or DELETE.']
    >>> isSafeishQuery('INSERT INTO some_table VALUES(1, 2, 3)', {})
    Traceback (most recent call last):
        ...
    ValidationError: [u'Queries may not contain INSERT, UPDATE or DELETE.']
    """
    test_value = field_data.upper()
    for keyword in ['INSERT', 'UPDATE', 'DELETE']:
        if keyword in test_value:
            raise ValidationError(
                u'Queries may not contain INSERT, UPDATE or DELETE.')
