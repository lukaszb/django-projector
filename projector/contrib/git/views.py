import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied


from projector.contrib.git.utils import is_git_request
from projector.contrib.git.githttp import GitWebServer
from projector.views.project import ProjectView

from vcs.web.simplevcs.utils import log_error, ask_basic_auth, basic_auth
from vcs.web.simplevcs.signals import pre_clone, post_clone, pre_push, post_push


class ProjectGitBaseView(ProjectView):
    """
    Base view class for git http handler.
    """

    csrf_exempt = True

    def __init__(self, *args, **kwargs):
        obj = super(ProjectGitBaseView, self).__init__(*args, **kwargs)
        self.mimetype = 'text/plain'
        self.charset = settings.DEFAULT_CHARSET
        self.headers = {}
        return obj

    def __before__(self):
        if not is_git_request(self.request):
            logging.debug("Not a GIT request")
            #raise Http404
        logging.info("Git request\n%s %s" % (
            self.request.META['REQUEST_METHOD'], self.request.META['PATH_INFO']))
        logging.debug("Catched git request by %s view" % self.__class__.__name__)
        logging.debug("Path is: %s" % self.request.META['PATH_INFO'])
        logging.debug("Query is: %s" % self.request.META['QUERY_STRING'])

    def get_required_perms(self):
        if is_git_request(self.request):
            # Let undelying code verify permissions
            return []
        return super(ProjectGitBaseView, self).get_required_perms()


class ProjectGitHandler(ProjectGitBaseView):
    """
    Extra attributes:

    - ``type``: returns ``READ`` or ``WRITE`` value of ``Type`` subclass of
      ``projector.contrib.git.githttp.GitWebServer``. It specifies if user
      is reading from or writing into the repository.

    Signals:

    Basing on ``type`` attribute, git handler sends one of ``pre_clone``,
    ``post_clone``, ``pre_push`` or ``post_push`` signal from
    ``vcs.web.simplevcs.signals``.
    """

    def response(self, request, username, project_slug):
        try:
            self.send_pre_signals()

            auth_response = self.check_auth()
            if auth_response:
                return auth_response

            git_server = GitWebServer(self.project.repository)
            response = git_server.get_response(request)

            self.send_post_signals()
        except Exception, err:
            log_error(err)
            raise err
        return response

    @property
    def type(self):
        """
        Returns type of request (READ, WRITE or UNSPECIFIED).
        """
        if 'git-upload-pack' in self.request.META['PATH_INFO']:
            type = GitWebServer.Type.READ
        elif 'git-receive-pack' in self.request.META['PATH_INFO']:
            type = GitWebServer.Type.WRITE
        else:
            type = GitWebServer.Type.UNSPECIFIED
        return type

    def get_signal_info(self):
        return {
            'sender': self,
            'repo_path': self.project.repository.path,
            'ip': self.request.META.get('REMOTE_ADDR', ''),
            'username': self.request.user.username,
        }

    def send_pre_signals(self):
        if self.is_read():
            signal = pre_clone
        elif self.is_write():
            signal = pre_push
        else:
            # Don't send any signal if we can't recognize request
            return
        info = self.get_signal_info()
        return signal.send(**info)

    def send_post_signals(self):
        if self.is_read():
            signal = post_clone
        elif self.is_write():
            signal = post_push
        else:
            # Don't send any signal if we can't recognize request
            return
        info = self.get_signal_info()
        return signal.send(**info)

    def check_auth(self):
        if self.project.is_public() and not self.is_write():
            return None
        # Check if user have been already authorized or ask to
        self.request.user = basic_auth(self.request)
        if self.request.user is None:
            return ask_basic_auth(self.request,
                realm=self.project.config.basic_realm)

        if self.project.is_public() and self.is_write() and not\
            self.request.user.has_perm('can_write_to_repository', self.project):
            raise PermissionDenied

        if self.project.is_private() and not\
            self.request.user.has_perm('can_read_repository', self.project):
            raise PermissionDenied
        if self.project.is_private() and self.is_write() and not\
            self.request.user.has_perm('can_write_to_repository', self.project):
            raise PermissionDenied
        return

    def is_read(self):
        return self.type == GitWebServer.Type.READ

    def is_write(self):
        return self.type == GitWebServer.Type.WRITE

