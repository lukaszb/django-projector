"""
Management commands listeners needs to be stored within ``management`` module
inside app.
"""
import sys
import logging

from django.db.models import Count

from projector.models import Project, Config
from projector.settings import get_config_value

from guardian.shortcuts import get_perms, get_perms_for_model, assign

def update_project_permissions(sender, **kwargs):
    """
    Creates missing permissions for projects' authors.
    """
    project_permissions = get_perms_for_model(Project)
    project_perms_set = set((p.codename for p in project_permissions))
    for project in Project.objects.all().select_related('author'):
        perms = get_perms(project.author, project)
        perms_set = set(perms)

        missing_perms = project_perms_set.difference(perms_set)
        missing_perms.discard('add_project') # This is not project specific
        for perm in missing_perms:
            new_perm = assign(perm, project.author, project)
            msg = '[INFO] Adding permission %s' % new_perm
            if kwargs['verbosity'] >= 2:
                print msg

def put_missing_project_configs(sender, **kwargs):
    """
    Required for backword compatibility as Config is a new model.
    """
    project_count = Project.objects.count()
    config_count = Config.objects.count()

    if project_count > config_count:
        if kwargs['interactive'] is True:
            msg = ("There are %d projects without configuration"
                    % (project_count - config_count))
            logging.info(msg)
            answer = ''
            while answer.lower() not in ('yes', 'no', 'y', 'n'):
                prompt = 'Create missing configs [yes/no, default=yes]: '
                try:
                    answer = raw_input(prompt).lower()
                except (KeyboardInterrupt, EOFError):
                    sys.stderr.write('\nInterrupted by user - taken as "no"\n')
                    answer = 'no'
                if answer == '':
                    answer = 'yes'
                if answer in ('y', 'yes'):
                    projects = Project.objects\
                        .annotate(config_count=Count('config'))\
                        .filter(config_count=0)
                    for project in projects:
                        config = project.create_config()
                        msg = "[INFO] Created %s" % config
                        if kwargs['verbosity'] >= 1:
                            print msg
                elif answer in ('n', 'no'):
                    sys.stderr.write("[WARNING] Projector app may couse errors "
                        "due to missing config for projects\n")

def create_missing_repositories(sender, **kwargs):
    """
    If :setting:`CREATE_REPOSITORIES` is set to ``True`` and we found
    :model:`Project` instances without repository we need to create them.
    """
    projects = Project.objects.filter(repository=None)

    if projects.count() > 0:
        if kwargs['interactive'] is True:
            msg = "There are %d projects without repos" % projects.count()
            logging.info(msg)
            answer = ''
            while answer.lower() not in ('yes', 'y', 'no', 'n'):
                prompt = ('Create missing repos [yes/no, default=yes] '
                          '[default vcs backend is: %s]'
                          % get_config_value('DEFAULT_VCS_BACKEND'))
                try:
                    answer = raw_input(prompt).lower()
                except (KeyboardInterrupt, EOFError):
                    sys.stderr.write('\nInterrupted by user - taken as "no"\n')
                    answer = 'no'

                if answer == '':
                    answer = 'yes'

                if answer in ('y', 'yes'):
                    for project in projects:
                        repo = project.create_repository()
                        msg = "[INFO] Created %s" % repo
                        if kwargs['verbosity'] >= 1:
                            print msg
                elif answer in ('n', 'no'):
                    sys.stderr.write("Answered 'no'. There are still %d missing"
                                     " repositories" % projects.count())

