from django import newforms as forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import connection
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import create_update, list_detail

from officeaid.auth import is_admin, user_has_permission
from officeaid.forms.sql_reports import SQLReportParameterForm
from officeaid.models import SQLReport
from officeaid.utils import dtuple
from officeaid.views import SortHeaders
from officeaid.views.generic import add_object, edit_object

LIST_HEADERS = (
    (u'SQL Report', 'name'),
)

@login_required
def sql_report_list(request):
    """
    Lists SQL Reports.

    Only list SQL Reports which the logged-in user has access to, based
    on their role and the access type set on each SQL Report.
    """
    user_profile = request.user.get_profile()
    header_defs = LIST_HEADERS
    if user_profile.is_admin():
        header_defs = LIST_HEADERS + ((u'Access', 'access'),)
    sort_headers = SortHeaders(request, header_defs)
    queryset = SQLReport.objects.accessible_to_user(request.user)
    return list_detail.object_list(request,
        queryset.order_by(sort_headers.get_order_by()),
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='sql_report',
        template_name='sql_reports/sql_report_list.html', extra_context={
            'user_profile': user_profile,
            'headers': list(sort_headers.headers()),
        })

@user_has_permission(is_admin)
def add_sql_report(request):
    """
    Adds a new SQL Report.
    """
    return add_object(request, SQLReport,
        template_name='sql_reports/add_sql_report.html')

@user_has_permission(is_admin)
def sql_report_detail(request, sql_report_id):
    """
    Displays a SQL Report's details.
    """
    sql_report = get_object_or_404(SQLReport, pk=sql_report_id)
    return render_to_response('sql_reports/sql_report_detail.html', {
            'sql_report': sql_report,
        }, RequestContext(request))

@user_has_permission(is_admin)
def edit_sql_report(request, sql_report_id):
    """
    Edits an SQL Report.
    """
    return edit_object(request, SQLReport, sql_report_id,
        template_object_name='sql_report',
        template_name='sql_reports/edit_sql_report.html')

@user_has_permission(is_admin)
def delete_sql_report(request, sql_report_id):
    """
    Deletes a SQL report.
    """
    return create_update.delete_object(request, SQLReport,
        post_delete_redirect=reverse('sql_report_list'),
        object_id=sql_report_id, template_object_name='sql_report',
        template_name='sql_reports/delete_sql_report.html')

@login_required
def execute_sql_report(request, sql_report_id):
    """
    Executes a SQL Report.

    This can be a two-step process:

    If the SQL Report contains any placeholders for SQL parameters,
    display or process a form which allows the user to provide data for
    each parameter.

    If the report requires no SQL parameters or parameters have been
    provided, execute the report query and display the results.
    """
    sql_report = get_object_or_404(SQLReport, pk=sql_report_id)
    param_names = sql_report.get_sql_parameters()
    params = None
    if len(param_names) > 0:
        if request.method == 'POST':
            form = SQLReportParameterForm(param_names, request.POST)
            if form.is_valid():
                params = form.cleaned_data
        else:
            form = SQLReportParameterForm(param_names)
        if params is None:
            # We still need some user input
            return render_to_response('sql_reports/execute_sql_report.html', {
                    'sql_report': sql_report,
                    'form': form,
                }, RequestContext(request))
    else:
        params = {}

    if params is not None:
        # Execute the report query and display results
        cursor = connection.cursor()
        cursor.execute(sql_report.get_populated_query(params))
        rows = dtuple.fetchrows(cursor)
        headings = None
        results = None
        if len(rows) > 0:
            headings = sql_report.get_headings_from_query()
            results = []
            for row in rows:
                row_dict = row.asMapping()
                results.append([row_dict[heading] for heading in headings])
        return render_to_response('sql_reports/results.html', {
                'sql_report': sql_report,
                'headings': headings,
                'results': results,
            }, RequestContext(request))
