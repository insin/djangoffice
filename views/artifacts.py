import datetime

from django import newforms as forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import list_detail

from officeaid.models import Artifact, Job
from officeaid.views import permission_denied, send_file, SortHeaders
from officeaid.views.generic import add_object, edit_object

LIST_HEADERS = (
    (u'Description', None),
    (u'Type',        None),
    (u'File',        'file'),
    (u'Size',        None),
    (u'Created At',  'created_at'),
    (u'Updated At',  'updated_at'),
    (u'Access',      'access'),
)

@login_required
def artifact_list(request, job_number):
    """
    Lists Artifacts for the Job with the given number.

    Only list Atrifacts which the logged-in user has access to, based on
    their role and the access type set on each Artifact.
    """
    job = get_object_or_404(Job, number=int(job_number))
    if not job.is_accessible_to_user(request.user):
        return permission_denied(request)
    user_profile = request.user.get_profile()
    queryset = Artifact.objects.accessible_to_user(request.user).filter(job=job)
    sort_headers = SortHeaders(request, LIST_HEADERS)
    return list_detail.object_list(request,
        queryset.order_by(sort_headers.get_order_by()),
        paginate_by=settings.ITEMS_PER_PAGE, allow_empty=True,
        template_object_name='artifact',
        template_name='artifacts/artifact_list.html', extra_context={
            'job': job,
            'headers': list(sort_headers.headers()),
        })

@login_required
def add_artifact(request, job_number):
    """
    Adds an Artifact.
    """
    job = get_object_or_404(Job, number=int(job_number))
    if not job.is_accessible_to_user(request.user):
        return permission_denied(request)
    ArtifactForm = forms.form_for_model(Artifact, fields=('file', 'type',
                                        'description', 'access'))
    if request.method == 'POST':
        form = ArtifactForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            artifact = form.save(commit=False)
            artifact.job = job
            artifact.created_at = datetime.datetime.now()
            artifact.updated_at = artifact.created_at
            artifact.save()
            request.user.message_set.create(
                message=u'The %s was added successfully.' \
                        % Artifact._meta.verbose_name)
            return HttpResponseRedirect(reverse('artifact_list',
                                                args=(job_number,)))
    else:
        form = ArtifactForm()
    return render_to_response('artifacts/add_artifact.html', {
            'form': form,
            'job': job,
        }, RequestContext(request))

@login_required
def artifact_detail(request, job_number, artifact_id):
    """
    Displays an Artifact's details.
    """
    job = get_object_or_404(Job, number=int(job_number))
    artifact = get_object_or_404(Artifact, job=job, pk=artifact_id)
    if not job.is_accessible_to_user(request.user) or \
       not artifact.is_accessible_to_user(request.user):
        return permission_denied(request)
    return render_to_response('artifacts/artifact_detail.html', {
        'artifact': artifact,
        'job': job,
    }, RequestContext(request))

@login_required
def download_artifact(request, job_number, artifact_id):
    """
    Sends an Artifact for download.
    """
    artifact = get_object_or_404(Artifact.objects.accessible_to_user(request.user),
                                 pk=artifact_id)
    return send_file(artifact.get_file_filename())

@login_required
def edit_artifact(request, job_number, artifact_id):
    """
    Edits an Artifact.
    """
    job = get_object_or_404(Job, number=int(job_number))
    artifact = get_object_or_404(Artifact, job=job, pk=artifact_id)
    if not job.is_accessible_to_user(request.user) or \
       not artifact.is_accessible_to_user(request.user):
        return permission_denied(request)
    ArtifactForm = forms.form_for_instance(artifact, fields=('file', 'type'
                                           'description', 'access'))
    if request.method == 'POST':
        form = ArtifactForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            artifact = form.save(commit=False)
            artifact.updated_at = datetime.datetime.now()
            artifact.save()
            request.user.message_set.create(
                message=u'The %s was edited successfully.' \
                        % Artifact._meta.verbose_name)
            return HttpResponseRedirect(reverse('artifact_list',
                                        args=(job_number,)))
    else:
        form = ArtifactForm()
    return render_to_response('artifacts/edit_artifact.html', {
            'form': form,
            'artifact': artifact,
            'job': job,
        }, RequestContext(request))

@login_required
def delete_artifact(request, job_number, artifact_id):
    """
    Deletes an Artifact.
    """
    raise NotImplementedError
