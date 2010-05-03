from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'projector.extras.users.views.user_homepage'),

    (r'^accounts/', include('registration.urls')),
    (r'^attachments/', include('attachments.urls')),
    (r'^projector/', include('projector.urls')),
    (r'^users/', include('projector.extras.users.urls')),

    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % settings.MEDIA_URL.strip('/'),
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
)

