from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from officeaid.auth import is_admin_or_manager, user_has_permission

@login_required
def report_list(request):
    return render_to_response('reports/report_list.html', {},
        RequestContext(request))

@user_has_permission(is_admin_or_manager)
def job_report_list(request):
    return render_to_response('reports/job_report_list.html', {},
        RequestContext(request))

@login_required
def timesheet_report_list(request):
    return render_to_response('reports/timesheet_report_list.html', {},
        RequestContext(request))

@user_has_permission(is_admin_or_manager)
def job_status_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def jobs_worked_on_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def job_expenses_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def jobs_missing_data_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def job_list_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def job_list_summary_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def job_full_report(request):
    raise NotImplementedError

@login_required
def timesheet_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def timesheet_status_report(request):
    raise NotImplementedError

@login_required
def user_report(request):
    raise NotImplementedError

@login_required
def annual_leave_report(request):
    raise NotImplementedError

@login_required
def client_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def invoiced_work_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def uninvoiced_work_report(request):
    raise NotImplementedError

@user_has_permission(is_admin_or_manager)
def developer_progress_report(request):
    raise NotImplementedError
