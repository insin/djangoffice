from decimal import Decimal
from django import template
from django.utils.encoding import force_unicode
from officeaid.utils.moneyfmt import moneyfmt

register = template.Library()

###########
# Filters #
###########

@register.filter
def money(amount, currency_symbol=''):
    """
    Formats the given value as a money value, with a leading currency
    symbol (if provided), commas every three digits, rounding and
    display to two decimal places.
    """
    if amount is None:
        return u'%s0.00' % currency_symbol
    elif not isinstance(amount, Decimal):
        amount = Decimal(amount)
    return force_unicode(moneyfmt(amount, curr=currency_symbol))
