import django.forms.models
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import (get_list_or_404, get_object_or_404,
    render_to_response)
from django.template import RequestContext

def add_object(request, model, fields=None, template_name=None,
               extra_context=None):
    """
    Generic view for creating new model instances using forms.
    """
    if extra_context is None: extra_context = {}
    ObjectForm = django.forms.models.modelform_factory(model, fields=fields)
    if request.method == 'POST':
        form = ObjectForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, 'The %s was created sucessfully.' \
                                      % model._meta.verbose_name)
            return HttpResponseRedirect(obj.get_absolute_url())
    else:
        form = ObjectForm()
    if not template_name:
        template_name = "%s/add_%s.html" % (model._meta.app_label,
                                            model._meta.object_name.lower())
    context = {
        'form': form,
    }
    for key, value in extra_context.items():
        if callable(value):
            context[key] = value()
        else:
            context[key] = value
    return render_to_response(template_name, context, RequestContext(request))

def edit_object(request, model, pk, fields=None, template_name=None,
        template_object_name='object', extra_context=None):
    """
    Generic view for editing model instances using forms.
    """
    if extra_context is None: extra_context = {}
    edit_obj = get_object_or_404(model, pk=pk)
    ObjectForm = django.forms.models.modelform_factory(model, fields=fields)
    if request.method == 'POST':
        form = ObjectForm(request.POST, instance=edit_obj)
        if form.is_valid():
            obj = form.save()
            messages.success(request, 'The %s was updated sucessfully.' \
                                      % model._meta.verbose_name)
            return HttpResponseRedirect(obj.get_absolute_url())
    else:
        form = ObjectForm(instance=edit_obj)
    if not template_name:
        template_name = "%s/edit_%s.html" % (model._meta.app_label,
                                             model._meta.object_name.lower())
    context = {
        template_object_name: edit_obj,
        'form': form,
    }
    for key, value in extra_context.items():
        if callable(value):
            context[key] = value()
        else:
            context[key] = value
    return render_to_response(template_name, context, RequestContext(request))

def delete_objects(request, model, pks, post_delete_redirect,
        template_name=None, template_object_name='object'):
    """
    Generic view for deleting multiple model instances, given their
    primary keys.
    """
    raise NotImplementedError
