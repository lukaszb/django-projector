from django.conf.urls.defaults import *
from django.conf import settings

from projector.feeds import LatestProjectsFeed

urlpatterns = patterns('projector.views',
    url(r'^$', 'project.project_list', name='projector_home'),
)

urlpatterns += patterns('projector.views.project_category',
    url(r'^categories/$', 'project_category_list', name='projector_project_category_list'),
    url(r'^categories/create/$', 'project_category_create', name='projector_project_category_create'),
    url(r'^categories/(?P<project_category_slug>[-\w]+)/$',
        'project_category_details', name='projector_project_category_details'),
)

urlpatterns += patterns('projector.views.project',
    url(r'^projects/$', 'project_list', name='projector_project_list'),
    url(r'^projects/create/$', 'project_create', name='projector_project_create'),
    #url(r'^projects/(?P<project_slug>[-\w]+)/$', 'project_details', name='projector_project_details'),
    url(r'^projects/(?P<project_slug>[-\w]+)/edit/$', 'project_edit', name='projector_project_edit'),
    url(r'^projects/(?P<project_slug>[-\w]+)/members/$', 'project_members', name='projector_project_members'),
    url(r'^projects/(?P<project_slug>[-\w]+)/members/add/$', 'project_members_add',
        name='projector_project_members_add'),
    url(r'^projects/(?P<project_slug>[-\w]+)/members/(?P<username>\w+)/$', 'project_members_manage',
        name='projector_project_members_manage'),

    url(r'^projects/(?P<project_slug>[-\w]+)/repository/(?P<rel_repo_url>.*)$',
        view='project_browse_repository',
        name='projector_project_browse_repository'),

    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/$', 'project_task_list', name='projector_task_list'),
)

urlpatterns += patterns('projector.views.task',
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/create/$', 'task_create', name='projector_task_create'),
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/$', 'task_details', name='projector_task_details'),
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/edit/$', 'task_edit', name='projector_task_edit'),
)

urlpatterns += patterns('projector.views.reports',
    url(r'^tasks/reports/$', 'task_reports', name='projector_task_reports'),
)

urlpatterns += patterns('projector.views.project',
    url(r'^projects/(?P<project_slug>[-\w]+)/.*', 'project_details', name='projector_project_details'),
)        

# ========== #
# Feeds dict #
# ========== #


feeds = {
    'projects': LatestProjectsFeed,
}

urlpatterns += patterns('',
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}),
)

# ========================== #
# restructuredText directive #
# ========================== #

#import rst_directive
#print "rst_directive loaded"
