from django.conf.urls.defaults import *

from projector.feeds import LatestProjectsFeed

urlpatterns = patterns('projector.views',
    url(r'^$', 'project.project_list', name='projector_home'),
    url(r'^settings/$', 'settings', name='projector_settings'),
)

urlpatterns += patterns('projector.views.project_category',
    url(r'^categories/$',
        view='project_category_list',
        name='projector_project_category_list'),
    url(r'^categories/create/$',
        view='project_category_create',
        name='projector_project_category_create'),
    url(r'^categories/(?P<project_category_slug>[-\w]+)/$',
        'project_category_details', name='projector_project_category_details'),
)

urlpatterns += patterns('projector.views.project',
    # Basic
    url(r'^projects/$',
        view='project_list',
        name='projector_project_list'),
    url(r'^projects/create/$',
        view='project_create',
        name='projector_project_create'),
    url(r'^projects/(?P<project_slug>[-\w]+)/edit/$',
        view='project_edit',
        name='projector_project_edit'),
    url(r'^projects/(?P<project_slug>[-\w]+)/$',
        view='project_details', name='projector_project_details'),

    # Milestones
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

    # Components
    url(r'^projects/(?P<project_slug>[-\w]+)/components/$',
        view='project_components',
        name='projector_project_components'),
    url(r'^projects/(?P<project_slug>[-\w]+)/components/create/$',
        view='project_component_add',
        name='projector_project_component_add'),
    url(r'^projects/(?P<project_slug>[-\w]+)/components/(?P<component_slug>[-\w]+)/$',
        view='project_component_detail',
        name='projector_project_component_detail'),
    url(r'^projects/(?P<project_slug>[-\w]+)/components/(?P<component_slug>[-\w]+)/edit/$',
        view='project_component_edit',
        name='projector_project_component_edit'),

    # Workflow
    url(r'^projects/(?P<project_slug>[-\w]+)/workflow/$',
        view='project_workflow_detail',
        name='projector_project_workflow_detail'),
    url(r'^projects/(?P<project_slug>[-\w]+)/workflow/edit/$',
        view='project_workflow_edit',
        name='projector_project_workflow_edit'),
    url(r'^projects/(?P<project_slug>[-\w]+)/workflow/create-status/$',
        view='project_workflow_add_status',
        name='projector_project_workflow_add_status'),

    # Members
    url(r'^projects/(?P<project_slug>[-\w]+)/members/$',
        view='project_members',
        name='projector_project_members'),
    url(r'^projects/(?P<project_slug>[-\w]+)/members/add/$',
        view='project_members_add',
        name='projector_project_members_add'),
    url(r'^projects/(?P<project_slug>[-\w]+)/members/(?P<username>\w+)/$',
        view='project_members_edit',
        name='projector_project_members_edit'),

    # Teams
    url(r'^projects/(?P<project_slug>[-\w]+)/teams/$',
        view='project_teams',
        name='projector_project_teams'),
    url(r'^projects/(?P<project_slug>[-\w]+)/teams/add/$',
        view='project_teams_add',
        name='projector_project_teams_add'),
    url(r'^projects/(?P<project_slug>[-\w]+)/teams/(?P<name>[-_ \w]+)/$',
        view='project_teams_edit',
        name='projector_project_teams_edit'),

    # Repository sources
    url(r'^projects/(?P<project_slug>[-\w]+)/src/diff/(?P<revision1>[\w]*)-(?P<revision2>[\w]*)/(?P<rel_repo_url>.*)$',
        view='project_file_diff',
        name='projector_project_file_diff'),
    url(r'^projects/(?P<project_slug>[-\w]+)/src/raw/(?P<revision>[\w]*)/(?P<rel_repo_url>.*)$',
        view='project_file_raw',
        name='projector_project_sources_raw'),
    url(r'^projects/(?P<project_slug>[-\w]+)/src/changesets/$',
        view='project_changesets',
        name='projector_project_changesets'),
    url(r'^projects/(?P<project_slug>[-\w]+)/src/(?P<revision>[\w]*)/(?P<rel_repo_url>.*)$',
        view='project_browse_repository',
        name='projector_project_sources_browse'),
    url(r'^projects/(?P<project_slug>[-\w]+)/src/$',
        view='project_browse_repository',
        name='projector_project_sources'),

    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/$',
        view='project_task_list',
        name='projector_task_list'),
)

# Tasks
urlpatterns += patterns('projector.views.task',
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/create/$',
        view='task_create', name='projector_task_create'),
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/$',
        view='task_details', name='projector_task_details'),
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/edit/$',
        view='task_edit', name='projector_task_edit'),
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/watch/$',
        view='task_watch', name='projector_task_watch'),
    url(r'^projects/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/unwatch/$',
        view='task_unwatch', name='projector_task_unwatch'),
)

urlpatterns += patterns('projector.views.reports',
    url(r'^tasks/reports/$', 'task_reports', name='projector_task_reports'),
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

