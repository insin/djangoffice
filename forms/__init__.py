import md5
import cPickle as pickle

from django import newforms as forms
from django.newforms.forms import BoundField

def security_hash(self, request, form):
    """
    Calculates the security hash for the given Form instance.

    This creates a list of the form field names/values in a deterministic
    order, pickles the result with the SECRET_KEY setting and takes an md5
    hash of that.
    """
    data = [(bf.name, bf.data) for bf in form] + [settings.SECRET_KEY]
    # Use HIGHEST_PROTOCOL because it's the most efficient. It requires
    # Python 2.3, but Django requires 2.3 anyway, so that's OK.
    pickled = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
    return md5.new(pickled).hexdigest()

class FilterBaseForm(forms.BaseForm):
    """Base form for forms which define filtering criteria."""

    def get_filters(self):
        """
        Handles the simplest possible filtering case, where each form
        field maps to a single query lookup and all query lookups should
        be ANDed, returning a dict mapping query lookups to values.

        Filter forms which wish to make use of this method must define
        a SEARCH_FILTERS class constant which is a list of two-tuples of
        field names and corresponding query lookups.
        """
        filters = {}
        if self.is_valid():
            for field, filter in self.SEARCH_FILTERS:
                if self.cleaned_data.has_key(field) and \
                   self.cleaned_data[field]:
                    filters[filter] = self.cleaned_data.get(field)
        return filters

    def get_params(self):
        """
        Returns a dict of parameters for this form, mapping populated
        field names to their values.
        """
        params = {}
        if self.is_valid():
            for field in self.fields.keys():
                if self.cleaned_data.has_key(field) and \
                   self.cleaned_data[field]:
                    params[field] = self.cleaned_data.get(field)
        return params

class HiddenBaseForm(forms.BaseForm):
    """
    Adds an ``as_hidden`` method to forms, which allows you to render
    a form using ``<input type="hidden">`` elements for every field.

    There is no error checking or display, as it is assumed you will
    be rendering a pre-validated form for resubmission, for example -
    when generating a preview of something based on a valid form's
    contents, resubmitting the same form via POST as confirmation.
    """
    def as_hidden(self):
        """
        Returns this form rendered entirely as hidden fields.
        """
        output = []
        for name, field in self.fields.items():
            bf = BoundField(self, field, name)
            output.append(bf.as_hidden())
        return u'\n'.join(output)
