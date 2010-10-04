from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'projector.views.users.UserHomepageView'),

    (r'^accounts/', include('registration.urls')),
    (r'^projector/', include('projector.urls')),
    (r'^richtemplates/', include('richtemplates.urls')),

    (r'^admin_tools/', include('admin_tools.urls')),
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % settings.MEDIA_URL.strip('/'),
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
)

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )

