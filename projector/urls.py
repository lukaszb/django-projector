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
    url(r'^projects/$',
        view='project_list',
        name='projector_project_list'),
    url(r'^projects/create/$',
        view='project_create',
        name='projector_project_create'),
    url(r'^projects/(?P<project_slug>[-\w]+)/edit/$',
        view='project_edit',
        name='projector_project_edit'),

    url(r'^projects/(?P<project_slug>[-\w]+)/milestones/$',
        view='project_milestones',
        name='projector_project_milestones'),    
    url(r'^projects/(?P<project_slug>[-\w]+)/milestones/create/$',
        view='project_milestones_add',
        name='projector_project_milestones_add'),
    url(r'^projects/(?P<project_slug>[-\w]+)/milestones/(?P<milestone_slug>[-\w]+)/$',
        view='project_milestone_detail',
        name='projector_project_milestone_detail'),
    url(r'^projects/(?P<project_slug>[-\w]+)/milestones/(?P<milestone_slug>[-\w]+)/edit/$',
        view='project_milestone_edit',
        name='projector_project_milestone_edit'),

    url(r'^projects/(?P<project_slug>[-\w]+)/members/$',
        view='project_members',
        name='projector_project_members'),
    url(r'^projects/(?P<project_slug>[-\w]+)/members/add/$',
        view='project_members_add',
        name='projector_project_members_add'),
    url(r'^projects/(?P<project_slug>[-\w]+)/members/(?P<username>\w+)/$',
        view='project_members_manage',
        name='projector_project_members_manage'),

    url(r'^projects/(?P<project_slug>[-\w]+)/repository/(?P<rel_repo_url>.*)$',
        view='project_browse_repository',
        name='projector_project_browse_repository'),
    url(r'^projects/(?P<project_slug>[-\w]+)/src/changesets/$',
        view='project_changesets',
        name='projector_project_changesets'),

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
    url(r'^projects/(?P<project_slug>[-\w]+)/?\??[-\w=\?\&/]*$', 'project_details', name='projector_project_details'),
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
