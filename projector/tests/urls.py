from django.conf.urls.defaults import *
from django.views.generic import simple
from django.conf import settings
from django.contrib import admin

import os

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'django.views.generic.simple.direct_to_template', {'template' : 'base.html'}),
    
    (r'^accounts/', include('registration.urls')),
    (r'^attachments/', include('attachments.urls')),
    (r'^projector/', include('projector.urls')),

    (r'^examples/', include('richtemplates.examples.urls')),
    (r'^admin/', include(admin.site.urls)),
)

