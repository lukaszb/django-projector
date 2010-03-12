from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import simple

def home(request, template_name='projector/home.html'):

    return simple.direct_to_template(request, {'template': template_name})
