from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('projector.extras.users.views',
    url(r'^$', 'user_list', name='projector_user_list'),
    url(r'^(?P<username>\w+)/$', 'profile_detail', name='projector_users_profile_detail'),
    url(r'^(?P<username>\w+)/edit/$', 'profile_edit', name='projector_users_profile_edit'),
)

