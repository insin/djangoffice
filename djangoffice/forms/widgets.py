from django import forms
from django.forms import widgets
from django.utils.encoding import force_unicode
from django.utils.html import escape
from django.utils.safestring import mark_safe

class DateInput(widgets.Input):
    input_type = 'text'

    def __init__(self, attrs=None):
        self.attrs = {'class': 'date', 'size': '10'}
        if attrs:
            self.attrs.update(attrs)

class HourInput(widgets.Input):
    input_type = 'text'

    def __init__(self, attrs=None):
        self.attrs = {'class': 'hours', 'size': '4'}
        if attrs:
            self.attrs.update(attrs)

class MoneyInput(widgets.Input):
    input_type = 'text'

    def __init__(self, attrs=None):
        self.attrs = {'class': 'money'}
        if attrs:
            self.attrs.update(attrs)

class TableSelectMultiple(forms.SelectMultiple):
    """
    Provides selection of items via checkboxes, with a table row
    being rendered for each item, the first cell in which contains the
    checkbox.

    When providing choices for this field, give the item as the second
    item in all choice tuples. For example, where you might have
    previously used::

        field.choices = [(item.id, item.name) for item in item_list]

    ...you should use::

        field.choices = [(item.id, item) for item in item_list]
    """
    def __init__(self, item_attrs, *args, **kwargs):
        """
        item_attrs
            Defines the attributes of each item which will be displayed
            as a column in each table row, in the order given.

            Any callable attributes specified will be called and have
            their return value used for display.

            All attribute values will be escaped.
        """
        super(TableSelectMultiple, self).__init__(*args, **kwargs)
        self.item_attrs = item_attrs

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = []
        str_values = set([force_unicode(v) for v in value]) # Normalize to strings.
        for i, (option_value, item) in enumerate(self.choices):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            output.append(u'<tr><td>%s</td>' % rendered_cb)
            for attr in self.item_attrs:
                if callable(getattr(item, attr)):
                    content = getattr(item, attr)()
                else:
                    content = getattr(item, attr)
                output.append(u'<td>%s</td>' % escape(content))
            output.append(u'</tr>')
        return mark_safe(u'\n'.join(output))
