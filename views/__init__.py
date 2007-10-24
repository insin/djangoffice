import mimetypes
import os

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'

class SortHeaders:
    """
    Table sorting utility class.

    Handles generation of an argument for the Django ORM's ``order_by``
    method and generation of table headers which reflect the currently
    selected sort, based on defined table headers with matching sort
    criteria.

    Based in part on the Django Admin application's ``ChangeList``
    functionality.
    """
    def __init__(self, request, headers, default_order_field=None,
            default_order_type='asc', additional_params=None):
        """
        request
            The request currently being processed - the current sort
            order field and type are determined based on GET
            parameters.

        headers
            A list of two-tuples of header text and matching ordering
            criteria for use with the Django ORM's ``order_by`` method.
            A criterion of ``None`` indicates that a header is not
            sortable.

        default_order_field
            The index of the header definition to be used for default
            ordering and when an invalid or non-sortable header is
            specified in GET parameters. If not specified, the index of
            the first sortable header will be used.

        default_order_type
            The default type of ordering used - must be one of ``'asc``
            or ``'desc'``.

        additional_params:
            Query parameters which should always appear in sort links,
            specified as a dictionary mapping parameter names to values.
            For example, this might contain the current page number if
            you're sorting a paginated list of items.
        """
        if default_order_field is None:
            for i, (header, query_lookup) in enumerate(headers):
                if query_lookup is not None:
                    default_order_field = i
                    break
        if default_order_field is None:
            raise AttributeError(u'No default_order_field was specified and none of the header definitions given were sortable.')
        if default_order_type not in ('asc', 'desc'):
            raise AttributeError(u'If given, default_order_type must be one of \'asc\' or \'desc\'.')
        if additional_params is None:
            additional_params = {}

        self.header_defs = headers
        self.additional_params = additional_params
        self.order_field = default_order_field
        self.order_type = default_order_type

        # Determine order field and order type for the current request
        params = dict(request.GET.items())
        if ORDER_VAR in params:
            try:
                new_order_field = int(params[ORDER_VAR])
                if headers[new_order_field][1] is not None:
                    self.order_field = new_order_field
            except (IndexError, ValueError):
                pass # Use the default
        if ORDER_TYPE_VAR in params and \
           params[ORDER_TYPE_VAR] in ('asc', 'desc'):
            self.order_type = params[ORDER_TYPE_VAR]

    def headers(self):
        """
        Generates dicts containing header and sort link details for all
        defined headers.
        """
        for i, (header, order_criterion) in enumerate(self.header_defs):
            th_classes = []
            new_order_type = 'asc'
            if i == self.order_field:
                th_classes.append('sorted %sending' % self.order_type)
                new_order_type = {'asc': 'desc', 'desc': 'asc'}[self.order_type]
            yield {
                'text': header,
                'sortable': order_criterion is not None,
                'url': self.get_query_string({
                    ORDER_VAR: i,
                    ORDER_TYPE_VAR: new_order_type
                 }),
                'class_attr': th_classes and ' class="%s"' % ' '.join(th_classes) or '',
            }

    def get_query_string(self, params):
        """
        Creates a query string from the given dictionary of parameters,
        including any additonal parameters which should always be
        present.
        """
        params.update(self.additional_params)
        return '?%s' % '&amp;'.join(['%s=%s' % (param, value) \
                                     for param, value in params.items()])

    def get_order_by(self):
        """
        Creates an ordering criterion based on the current order field
        and order type, for use with the Django ORM's ``order_by``
        method.
        """
        return '%s%s' % (
            self.order_type == 'desc' and '-' or '',
            self.header_defs[self.order_field][1],
        )

def permission_denied(request, message=u''):
    """
    General view to be used when a user attempts to perform an action
    for which they do not have permission.
    """
    return render_to_response('permission_denied.html', {
            message: message,
        }, RequestContext(request))

def send_file(filename):
    """
    Creates a response which sends a file for download, guessing its MIME
    type.

    Implementation based on http://www.satchmoproject.com/trac/browser/satchmo/trunk/satchmo/shop/views/download.py

    For this to work, your server must support the X-Sendfile header -
    Apache and lighttpd should both work with the headers used.

    For Apache, you will need `mod_xsendfile`_.

    For lighttpd, allow-x-send-file must be enabled.

    .. _`mod_xsendfile`: http://tn123.ath.cx/mod_xsendfile/
    """
    response = HttpResponse()
    response['X-Sendfile'] = response['X-LIGHTTPD-send-file'] = filename
    mimetype = mimetypes.guess(filename)[0]
    response['Content-Type'] = mimetype or 'application/octet-stream'
    response['Content-Disposition'] = \
        'attachment; filename=%s' % os.path.split(filename)[1]
    response['Content-Length'] = os.stat(filename).st_size
    return response

# Make the menu tag global
from django.template import add_to_builtins
add_to_builtins('officeaid.templatetags.menu')
