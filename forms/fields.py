from django import newforms as forms
from django.core import validators
from django.newforms.fields import EMPTY_VALUES
from django.newforms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.text import capfirst

class DynamicModelChoiceField(forms.Field):
    def __init__(self, model, *args, **kwargs):
        super(DynamicModelChoiceField, self).__init__(*args, **kwargs)
        self.model = model
        widget_kwargs = {}
        if 'display_template' in kwargs:
            widget_kwargs['display_template'] = kwargs.pop('display_template')
        if 'display_func' in kwargs:
            widget_kwargs['display_func'] = kwargs.pop('display_func')
        self.widget = DynamicChoice(model, **widget_kwargs)

    def clean(self, value):
        """
        Validates that the input is a valid primary key for the model and
        that a model instance with the given primary key exists.
        """
        value = super(DynamicModelChoiceField, self).clean(value)
        if value in EMPTY_VALUES:
            value = None
        else:
            try:
                value = self.model._meta.pk.to_python(value)
            except validators.ValidationError, e:
                raise forms.ValidationError(e.messages[0])
            else:
                if not self.model._default_manager.filter(pk=value).count():
                    raise forms.ValidationError(
                        u'This field must specify an existing %s' % \
                            capfirst(self.model._meta.verbose_name))
        return value

class DynamicChoice(forms.Widget):
    """
    Provides a hidden field to be manipulated on the client side when
    implementing dynamic selection of an instance of a given model, with
    the primary key of the selected instance being stored in the field.

    If a valid primary key has been specified, the string equivalent of
    the appropriate model instance will also be be displayed.
    """
    def __init__(self, model, attrs=None,
                 display_template=u' <span id="%(field_name)s_display">%(item)s</span>',
                 display_func=lambda x: unicode(x)):
        self.model = model
        self.attrs = attrs or {}
        self.display_template = display_template
        self.display_func = display_func

    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, type='hidden', name=name)
        display_text = ''
        if value != '':
            final_attrs['value'] = force_unicode(value)
            try:
                instance = self.model._default_manager.get(pk=value)
                display_text = self.display_template % {
                    'field_name': name,
                    'item': self.display_func(instance),
                }
            except self.model.DoesNotExist:
                pass
        return u'<input%s>%s' % (flatatt(final_attrs), display_text)

class MultipleDynamicModelChoiceField(forms.ChoiceField):
    widget = forms.SelectMultiple

    def __init__(self, model, display_func=lambda x: unicode(x), *args, **kwargs):
        self.model = model
        self.display_func = display_func
        super(MultipleDynamicModelChoiceField, self).__init__(*args, **kwargs)
        # HACK - assignment to self.initial in Field.__init__ isn't using
        #        the property this class defines.
        if 'initial' in kwargs:
            self.initial = kwargs['initial']

    def _get_initial(self):
        return self._initial

    def _set_initial(self, value):
        # Setting initial also sets choices on the widget.
        self._initial = value
        if value is not None and len(value):
            self.choices = [(i.pk, self.display_func(i)) for i in \
                self.model._default_manager.filter(pk__in=value)]

    initial = property(_get_initial, _set_initial)

    def clean(self, value):
        """
        Validates that the input is a list of valid primary keys for the
        model and that model instances with the given primary keys exist.
        """
        if self.required and not value:
            raise ValidationError(ugettext(u'This field is required.'))
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(ugettext(u'Enter a list of values.'))
        # Validate that each value in the value list is a valid primary key.
        pk_field = self.model._meta.pk
        try:
            pk_values = [pk_field.to_python(v) for v in value]
        except validators.ValidationError, e:
            raise forms.ValidationError(e.messages[0])
        else:
            if len(value) != \
               self.model._default_manager.filter(pk__in=pk_values).count():
                raise forms.ValidationError(
                    u'This field must specify existing %s' % \
                        capfirst(self.model._meta.verbose_name_plural))
        return pk_values