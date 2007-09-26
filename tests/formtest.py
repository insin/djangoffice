import datetime

from django import newforms as forms
from django.contrib.auth.models import User
from django.test import TestCase

from officeaid.forms.fields import (DynamicChoice, DynamicModelChoiceField,
    MultipleDynamicModelChoiceField)

class FormTest(TestCase):
    """
    Tests for custom form fields and widgets.
    """
    fixtures = ['initial_test_data']

    def testDynamicChoiceWidget(self):
        w = DynamicChoice(User)
        # Defaults
        self.assertEquals(u'<input type="hidden" name="test">', w.render('test', None))
        self.assertEquals(u'<input type="hidden" name="test" value="1"> <span id="test_display">admin</span>',
            w.render('test', 1))
        # Non-existant or invalid PK given
        self.assertEquals(u'<input type="hidden" name="test" value="4">', w.render('test', 4))
        self.assertEquals(u'<input type="hidden" name="test" value="a">', w.render('test', 'a'))
        # Custom display template
        w = DynamicChoice(User, display_template=u' <span id="display_%(field_name)s">Currently selected: <strong>%(item)s</strong></span>')
        self.assertEquals(u'<input type="hidden" name="test" value="1"> <span id="display_test">Currently selected: <strong>admin</strong></span>',
            w.render('test', 1))
        # Custom display function
        w = DynamicChoice(User, display_func=lambda x: x.get_full_name())
        self.assertEquals(u'<input type="hidden" name="test" value="1"> <span id="test_display">Admin User</span>',
            w.render('test', 1))

    def testDynamicModelChoiceField(self):
        f = DynamicModelChoiceField(User)
        # Valid PK
        self.assertEquals(1, f.clean('1'))
        # Non-existant PK
        self.assertRaises(forms.ValidationError, f.clean, '4');
        # Invalid PK
        self.assertRaises(forms.ValidationError, f.clean, 'a');

    def testMultipleDynamicModelChoiceField(self):
        f = MultipleDynamicModelChoiceField(User)
        # Valid PKs
        self.assertEquals([1, 2, 3], f.clean(['1', '2', '3']))
        # Non-existant PK
        self.assertRaises(forms.ValidationError, f.clean, ['1', '2', '4']);
        # Invalid PK
        self.assertRaises(forms.ValidationError, f.clean, ['1', '2', 'a']);

        # Initial value should populate field and widget choices
        f.initial=[1]
        self.assertEquals([(1, u'admin')], f.choices)
        self.assertEquals([(1, u'admin')], f.widget.choices)
        f = MultipleDynamicModelChoiceField(User, initial=[1])
        self.assertEquals([(1, u'admin')], f.choices)
        self.assertEquals([(1, u'admin')], f.widget.choices)
