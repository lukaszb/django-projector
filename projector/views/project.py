import logging
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.utils.simplejson import dumps
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator

from projector.core.controllers import View
from projector.core.exceptions import ProjectorError
from projector.models import Project, State
from projector.forms import ProjectCreateForm, ProjectEditForm, ConfigForm,\
    ProjectForkForm
from projector.settings import get_config_value
from projector.signals import setup_project

from vcs.web.simplevcs.utils import get_mercurial_response, is_mercurial
from vcs.web.simplevcs.utils import log_error, basic_auth, ask_basic_auth
from vcs.web.simplevcs.exceptions import NotMercurialRequest

login_required_m = method_decorator(login_required)

class ProjectView(View):
    """
    Base class for all projector views.

    Logic should be implemented at ``response`` method.

    Would check necessary permissions defined by class attributes: ``perms``,
    ``perms_GET`` and ``perms_POST``.

    ``perms`` are always checked, ``perms_POST`` are additional checks which
    would be made for ``GET`` method requests only and ``perms_POST`` would be
    made for ``POST`` method requests.  ``perms_private`` would be checked for
    private projects only.

    .. note::
       This view class should be considered as abstract - it does not implement
       ``response`` method.

    **View attributes**

    * ``perms``: ``[]``
    * ``perms_private``: ``['view_project']``
    * ``perms_GET``: ``[]``
    * ``perms_POST``: ``[]``

    * ``template_error_name``:  ``projector/project/error.html``
    * ``template_pending_name``: ``projector/project/pending.html``

    **Required parameters**

    * ``request``: ``django.http.HttpRequest`` instance, which is always passed
      as first positional argument

    * ``username``:  :model:`Project` would be fetched using this parameter as
      ``User``'s ``username`` attribute lookup

    * ``project_slug``: :model:`Project` would be fetched using this parameter
      as :model:`Project`'s ``slug`` attribute lookup


    **Context variables**

    * ``project``: :model:`Project` instance fetched using provided parameters

    * ``STATES``: class describing project states (:class:`projector.models.State`)

    * ``project_root``: :model:`Project` instance which is a root in requested
      project forks tree. If requested project is a root, value of this variable
      would be same as ``project`` variable.

    * ``forks``: list of :model:`Project` instances which are fork of the
      requested project. If requested project is a root, list would contain only
      requested project (would be same as ``project`` variable).

    * ``user_fork``: :model:`Project` instance representing ``request.user``'s
      own fork of requested project. If user haven't forked this project then
      ``user_fork`` would be ``None``.

    """

    perms = []
    perms_private = ['view_project']
    perms_GET = []
    perms_POST = []

    template_error_name = 'projector/project/error.html'
    template_pending_name = 'projector/project/pending.html'

    def __init__(self, request, username=None, project_slug=None, *args,
            **kwargs):
        self.request = request
        self.project = get_object_or_404(Project, slug=project_slug,
            author__username=username)
        self.author = self.project.author
        self.check_permissions()
        super(ProjectView, self).__init__(request=request, username=username,
            project_slug=project_slug, *args, **kwargs)
        self.context['project'] = self.project
        self.context['STATES'] = State

        # Set forks without additional queries if is a root (not forked project)
        if self.project.is_root():
            self.context['forks'] = [self.project]
            self.context['project_root'] = self.project
            if request.user.is_anonymous():
                self.context['user_fork'] = None
            elif request.user == self.project.author:
                self.context['user_fork'] = self.project
            else:
                self.context['user_fork'] = self.project.get_fork_for_user(
                    request.user)
        else:
            forks = self.project.get_all_forks()
            self.context['forks'] = forks
            self.context['project_root'] = self.project.get_root()
            user_fork = None
            if request.user.is_anonymous():
                self.context['user_fork'] = None
            else:
                for fork in forks:
                    if fork.author_id == request.user.id:
                        user_fork = fork
                        break
            self.context['user_fork'] = user_fork


    def __after__(self):
        if self.project.state == State.ERROR:
            return render_to_response(self.template_error_name, self.context,
                RequestContext(self.request))
        if self.project.is_pending():
            return render_to_response(self.template_pending_name, self.context,
                RequestContext(self.request))

    def get_required_perms(self):
        """
        Returns list of required perms based on instance's attributes.
        If modified, make sure it's thread-safe, i.e. don't change self.perms
        directly but create new temporary list of permissions.
        """
        perms = [p for p in self.perms]

        if self.request.method == 'GET':
            perms += [p for p in self.perms_GET]
        elif self.request.method == 'POST':
            perms += [p for p in self.perms_POST]

        if self.project.is_private():
            perms += [p for p in self.perms_private]
        perms = set(perms)
        return perms

    def check_permissions(self):
        """
        Checks if user has permissions to call this view. By default, this
        method would perform checks using requested :model:`Project` instance
        and permission list retrieved by ``get_required_perms`` method.
        """
        # Owner's are always allowed to do anything with their projects
        # - this would make less database hits
        if self.project.author == self.request.user:
            return
        perms = self.get_required_perms()
        for perm in perms:
            if not self.request.user.has_perm(perm, self.project):
                if settings.DEBUG:
                    logging.debug("User %s has no permission %s for project %s"
                        % (self.request.user, perm, self.project))
                raise PermissionDenied()


class ProjectState(ProjectView):

    def __after__(self):
        pass

    def response(self, request, username, project_slug):
        data = {'state': self.project.state}
        if self.project.state == State.ERROR:
            data['error_text'] = self.project.error_text or ''
        json_data = dumps(data)
        return HttpResponse(json_data, content_type='application/json')


class ProjectDetailView(ProjectView):
    """
    Returns selected project's detail for user given in ``request``.
    We make necessary permission checks *after* dispatching between
    normal and mercurial request, as mercurial requests has it's own
    permission requirements.

    **View attributes**

    * ``template_name``: ``projector/project/detail.html``

    * ``csrf_exempt``: ``True``

    """

    template_name = 'projector/project/detail.html'
    csrf_exempt = True

    def get_required_perms(self):
        """
        Returns empty list if request is identified as *mercurial request*.
        For mercurial requests lets underlying view to manage permissions
        checks.
        """
        if is_mercurial(self.request):
            return []
        return super(ProjectDetailView, self).get_required_perms()

    def response(self, request, username, project_slug):
        try:

            if is_mercurial(request):
                return self.response_hg(request, self.project)
            last_part = request.path.split('/')[-1]
            if last_part and last_part != project_slug:
                raise Http404("Not a mercurial request and path longer than "
                    " should be: %s" % request.path)

            # project is injected into the context at ProjectView constructor
            # so we do not need to add it here
            return self.context

        except Exception, err:
            dont_log_exceptions = (PermissionDenied,)
            if not isinstance(err, dont_log_exceptions):
                log_error(err)
            raise err

    def response_hg(self, request, project):
        return _project_detail_hg(request, project)


def _project_detail_hg(request, project):
    """
    Wrapper for vcs.web.simplevcs.views.hgserve view as before we go any further
    we need to check permissions.
    TODO: Should use higher level simplevcs method
    """
    if not is_mercurial(request):
        msg = "_project_detail_hg called for non mercurial request"
        logging.error(msg)
        raise NotMercurialRequest(msg)

    if request.method not in ('GET', 'POST'):
        raise NotMercurialRequest("Only GET/POST methods are allowed, got %s"
            % request.method)
    PUSH_SSL = get_config_value('HG_PUSH_SSL') and 'true' or 'false'
    # Allow to read from public projects
    if project.is_public() and request.method == 'GET':
        mercurial_info = {
            'repo_path': project._get_repo_path(),
            'push_ssl': PUSH_SSL,
        }
        return get_mercurial_response(request, **mercurial_info)

    # Check if user have been already authorized or ask to
    request.user = basic_auth(request)
    if request.user is None:
        return ask_basic_auth(request,
            realm=project.config.basic_realm)

    if project.is_private() and request.method == 'GET' and\
        not request.user.has_perm('can_read_repository', project):
        raise PermissionDenied("User %s cannot read repository for "
            "project %s" % (request.user, project))
    elif request.method == 'POST' and\
        not request.user.has_perm('can_write_to_repository',project):
        raise PermissionDenied("User %s cannot write to repository "
            "for project %s" % (request.user, project))

    mercurial_info = {
        'repo_path': project._get_repo_path(),
        'push_ssl': PUSH_SSL,
    }

    if request.user and request.user.is_active:
        mercurial_info['allow_push'] = request.user.username

    response = get_mercurial_response(request, **mercurial_info)
    return response


class ProjectListView(View):
    """
    Project listing view.

    **View attributes**

    * ``template_name``: ``projector/project/list.html``

    **Additional context variables**

    * ``project_list``: :model:`Project` queryset filtered for request's user.
      Additionally, projects are annotated with :model:`Task` count (available
      as ``task__count`` attribute on each retrieved project).

    """

    template_name = 'projector/project/list.html'

    def response(self, request):
        project_list = Project.objects.for_user(user=request.user)\
            .annotate(Count('task', distinct=True))
        context = {
            'project_list' : project_list,
        }
        return context


class ProjectCreateView(View):
    """
    New project creation view.

    .. seealso:: :ref:`projects-basics-create`

    **Additional context variables**

    * ``form``: :form:`ProjectCreateForm`
    """

    template_name = 'projector/project/create.html'

    @login_required_m
    def response(self, request, username=None):
        # TODO: what with username param? should it be required?
        # it's not used for now...
        project = Project(
            author=request.user,
        )
        form = ProjectCreateForm(request.POST or None, instance=project,
            initial={'public': u'private'})
        if request.method == 'POST' and form.is_valid() and \
                self.can_create(request.user, request):
            project = form.save()
            return redirect(project.get_absolute_url())
        context = {
            'form' : form,
        }
        return context

    @staticmethod
    def can_create(user, request=None):
        """
        Checks if given user can create project. Note that this function will
        not validate project itself. If
        :setting:`PROJECTOR_MILIS_BETWEEN_PROJECT_CREATION` is greater than
        miliseconds since last time this user has created a project then he or
        she is allowed to create new one.

        If user is trying to create more project than specified by
        :setting:`PROJECTOR_MAX_PROJECTS_PER_USER` configuration value then we
        disallow.

        If request is given, sends messages.
        """

        def send_error(request, message):
            if request:
                messages.error(request, message)

        try:
            date = Project.objects.filter(author=user)\
                .only('name', 'created_at')\
                .order_by('-created_at')[0].created_at
            delta = datetime.datetime.now() - date
            milis = delta.seconds * 1000
            need_to_wait = get_config_value('MILIS_BETWEEN_PROJECT_CREATION')\
                - milis
            need_to_wait /= 1000
            if need_to_wait > 0:
                send_error(request, _("You would be allowed to create a new "
                    "project in %s seconds" % need_to_wait))
                return False
        except IndexError:
            pass
        count = user.project_set.count()
        too_many = count - get_config_value('MAX_PROJECTS_PER_USER')
        if too_many > 0:
            send_error(request, _("You cannot create more projects"))
            return False
        return True


class ProjectForkView(ProjectView):
    """
    Project fork (internal fork) view.

    .. seealso:: :ref:`projects-forking`

    **Additional context variables**

    * ``form``: :form:`ProjectForkForm`

    """

    template_name = 'projector/project/fork.html'

    @login_required_m
    def response(self, request, username, project_slug):
        user_fork = self.project.get_fork_for_user(request.user)
        if user_fork:
            messages.warning(request, _("User has already forked this project"))
            return redirect(user_fork.get_absolute_url())

        form = ProjectForkForm(request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                # TODO: Move can_create from ProjectCreateView class
                ProjectCreateView.can_create(request.user, request)
                try:
                    fork = self.project.fork(user=request.user)
                    setup_project.send(sender=Project, instance=fork)
                    return redirect(fork.get_absolute_url())
                except ProjectorError, err:
                    messages.error(request, str(err))
                return redirect(self.project.get_absolute_url())
        self.context['form'] = form
        return self.context


class ProjectEditView(ProjectView):
    """
    Update project view.

    **Additional context variables**

    * ``form``: :form:`ProjectEditForm`

    * ``form_config``: :form:`ConfigForm`

    """

    template_name = 'projector/project/edit.html'
    perms = ['view_project', 'change_project', 'admin_project']

    def validate_project_form(self, request):
        public_val = self.project.is_public() and u'public' or u'private'
        if request.method == 'POST' and \
                request.POST.get('submit_project', False):
            form = ProjectEditForm(request.POST, instance=self.project,
                initial={'public': public_val})
            if form.is_valid():
                msg = _("Project edited successfully")
                self.project = form.save()
                messages.success(request, msg)
                return redirect(self.project.get_edit_url())
            else:
                msg = _("Form has not validated")
                messages.error(request, msg)
        else:
            form = ProjectEditForm(instance=self.project,
                initial={'public': public_val})
        self.context['form'] = form

    def validate_config_form(self, request):
        if request.method == 'POST' and \
                request.POST.get('submit_config', False):
            form = ConfigForm(request.POST, instance=self.project.config)
            if form.is_valid():
                form.instance.editor = request.user
                form.save()
                msg = _("Project's configuration updated successfully")
                messages.success(request, msg)
            else:
                msg = _("Errors occured while trying to update "
                            "project's configuration")
                messages.error(request, msg)
        else:
            form = ConfigForm(instance=self.project.config)
        self.context['form_config'] = form

    @login_required_m
    def response(self, request, username, project_slug):
        self.context['project'] = self.project
        result = self.validate_project_form(request)
        if result:
            return result
        result = self.validate_config_form(request)
        if result:
            return result
        return self.context


