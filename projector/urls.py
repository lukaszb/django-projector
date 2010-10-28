from django.conf.urls.defaults import *

from projector.feeds import LatestProjectsFeed

urlpatterns = patterns('projector.views',
    url(r'^$', 'project.ProjectListView', name='projector_home'),
)

urlpatterns += patterns('projector.views.project_category',
    url(r'^categories/$',
        view='project_category_list',
        name='projector_project_category_list'),
    url(r'^categories/create/$',
        view='project_category_create',
        name='projector_project_category_create'),
    url(r'^categories/(?P<project_category_slug>[-\w]+)/$',
        'project_category_detail', name='projector_project_category_detail'),
)

# User dashboard
urlpatterns += patterns('projector.views.users',
    url(r'^dashboard/convert-to-team/$',
        view = 'UserDashboardConvert2TeamView',
        name = 'projector_dashboard_convert_to_team'),

    url(r'^dashboard/external-fork/$',
        view = 'UserDashboardForkView',
        name = 'projector_dashboard_fork'),

    url(r'^dashboard/add-member/$',
        view = 'UserDashboardAddMember',
        name = 'projector_dashboard_add_member'),

    url(r'^dashboard/$',
        view = 'UserDashboardView',
        name = 'projector_dashboard'),
)

urlpatterns += patterns('projector.views.project',
    # Basic
    url(r'^projects/$',
        view='ProjectListView',
        name='projector_project_list'),
    url(r'^projects/create-project/$',
        view='ProjectCreateView',
        name='projector_project_create'),
    url(r'^projects/fork-external-project/$',
        view='ProjectCreateView',
        name='projector_project_fork_external'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+?)\.git/',
        include('projector.contrib.git.urls')),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/admin/$',
        view='ProjectEditView',
        name='projector_project_edit'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/fork/$',
        view='ProjectForkView',
        name='projector_project_fork'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/state/$',
        view='ProjectState',
        name='projector_project_state'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/$',
        view='ProjectDetailView', name='projector_project_detail'),
)

# Milestones
urlpatterns += patterns('projector.views.project_milestone',
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/milestones/$',
        view='MilestoneListView',
        name='projector_project_milestones'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/milestones/gantt/$',
        view='MilestoneGanttView',
        name='projector_project_milestones_gantt'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/milestones/create/$',
        view='MilestoneCreateView',
        name='projector_project_milestone_add'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/milestones/(?P<milestone_slug>[-\w]+)/$',
        view='MilestoneDetailView',
        name='projector_project_milestone_detail'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/milestones/(?P<milestone_slug>[-\w]+)/edit/$',
        view='MilestoneEditView',
        name='projector_project_milestone_edit'),
)

# Components
urlpatterns += patterns('projector.views.project_component',
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/components/$',
        view='ComponentListView',
        name='projector_project_components'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/components/create/$',
        view='ComponentCreateView',
        name='projector_project_component_add'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/components/(?P<component_slug>[-\w]+)/$',
        view='ComponentDetailView',
        name='projector_project_component_detail'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/components/(?P<component_slug>[-\w]+)/edit/$',
        view='ComponentEditView',
        name='projector_project_component_edit'),
)

# Workflow
urlpatterns += patterns('projector.views.project_workflow',
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/workflow/$',
        view='WorkflowDetailView',
        name='projector_project_workflow_detail'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/workflow/edit/$',
        view='WorkflowEditView',
        name='projector_project_workflow_edit'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/workflow/create-status/$',
        view='WorkflowAddStatusView',
        name='projector_project_workflow_add_status'),
)

# Members
urlpatterns += patterns('projector.views.project_member',
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/members/$',
        view='MemberListView',
        name='projector_project_member'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/members/add/$',
        view='MemberAddView',
        name='projector_project_member_add'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/members/(?P<member_username>\w+)/$',
        view='MemberEditView',
        name='projector_project_member_edit'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/members/(?P<member_username>\w+)/delete/$',
        view='MemberDeleteView',
        name='projector_project_member_delete'),
)

# Teams
urlpatterns += patterns('projector.views.project_team',
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/teams/$',
        view='TeamListView',
        name='projector_project_teams'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/teams/add/$',
        view='TeamAddView',
        name='projector_project_teams_add'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/teams/(?P<name>[-_ \w]+)/$',
        view='TeamEditView',
        name='projector_project_teams_edit'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/teams/(?P<name>[-_ \w]+)/delete/$',
        view='TeamDeleteView',
        name='projector_project_teams_delete'),
)

# Project's repository browsing
urlpatterns += patterns('projector.views.project_repository',
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/diff/(?P<revision_old>[\w]*)-(?P<revision_new>[\w]*)/(?P<rel_repo_url>.*)$',
        view='RepositoryFileDiff',
        name='projector_project_sources_diff'),

    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/quickstart/$',
        view='RepositoryQuickstart',
        name='projector_project_sources_quickstart'),

    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/raw/(?P<revision>[\w]*)/(?P<rel_repo_url>.*)$',
        view='RepositoryFileRaw',
        name='projector_project_sources_raw'),

    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/annotate/(?P<revision>[\w]*)/(?P<rel_repo_url>.*)$',
        view='RepositoryFileAnnotate',
        name='projector_project_sources_annotate'),

    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/changesets/$',
        view='RepositoryChangesetList',
        name='projector_project_changesets'),

    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/changesets/(?P<revision>[\w]*)/$',
        view='RepositoryChangesetDetail',
        name='projector_project_changeset_detail'),

    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/(?P<revision>[\w]*)/(?P<rel_repo_url>.*)$',
        view='RepositoryBrowse',
        name='projector_project_sources_browse'),

    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/src/$',
        view='RepositoryBrowse',
        name='projector_project_sources'),
)

# Tasks
urlpatterns += patterns('projector.views.project_task',
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/tasks/$',
        view='TaskListView',
        name='projector_task_list'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/tasks/data/$',
        view='TaskListDataView',
        name='projector_task_list_data'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/tasks/create/$',
        view='TaskCreateView',
        name='projector_task_create'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/$',
        view='TaskDetailView',
        name='projector_task_detail'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/edit/$',
        view='TaskEditView',
        name='projector_task_edit'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/watch/$',
        view='TaskWatchView',
        name='projector_task_watch'),
    url(r'^(?P<username>[-\w]+)/(?P<project_slug>[-\w]+)/tasks/(?P<task_id>\d+)/unwatch/$',
        view='TaskUnwatchView',
        name='projector_task_unwatch'),
)

urlpatterns += patterns('projector.views.users',
    url(r'^(?P<username>\w+)/$',
        view = 'UserProfileDetailView',
        name = 'projector_users_profile_detail'),
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

