import logging

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required, permission_required,\
    user_passes_test
from django.template import RequestContext
from django.views.generic import list_detail, create_update
from django.contrib.auth.decorators import login_required

from projector.models import Project, ProjectCategory, Membership
from projector.forms import ProjectForm

@login_required
def project_category_details(request, project_category_slug,
        template_name='projector/project_category/details.html'):
    logging.debug("project_category_details called")
    kwargs = {
        'queryset' : ProjectCategory.objects.all(),
        'slug' : project_category_slug,
        'template_name' : template_name,
        'template_object_name' : 'project_category',
        'extra_context' : {}
    }

    return list_detail.object_detail(request, **kwargs)

@login_required
@permission_required('projector.add_project_category')
def project_category_create(request, template_name='projector/project_category/create.html'):
    logging.debug("project_category_create called")
    kwargs = {
        'model' : ProjectCategory,
        'template_name' : template_name,
    }
    
    return create_update.create_object(request, **kwargs)

def project_category_list(request, template_name='projector/project_category/list.html'):
    logging.debug("project_category_list called")
    kwargs = {
        'queryset' : ProjectCategory.objects.all(),
        'template_name' : template_name,
        'template_object_name' : 'project_category',
    }
    
    return list_detail.object_list(request, **kwargs)

