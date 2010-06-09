from django.conf.urls.defaults import *

urlpatterns = patterns('projector.views.users',
    url(r'^$',
        view = 'UserListView',
        name = 'projector_user_list'),

    url(r'^(?P<username>\w+)/$',
        view = 'UserProfileDetailView',
        name = 'projector_users_profile_detail'),

    url(r'^(?P<username>\w+)/edit/$',
        view = 'UserProfileEditView',
        name = 'projector_users_profile_edit'),
)

