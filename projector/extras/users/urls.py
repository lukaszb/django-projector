from django.conf.urls.defaults import *

urlpatterns = patterns('projector.extras.users.views',
    url(r'^$',
        view = 'user_list',
        name = 'projector_user_list'),

    url(r'^(?P<username>\w+)/$',
        view = 'profile_detail',
        name = 'projector_users_profile_detail'),

    url(r'^(?P<username>\w+)/edit/$',
        view = 'profile_edit',
        name = 'projector_users_profile_edit'),
)

