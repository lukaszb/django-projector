import os
import logging

from django.conf import settings
from django.http import Http404, HttpResponse

from dulwich.server import Backend
from dulwich.web import HTTPGitApplication
from dulwich.web import HTTPGitRequest


from projector.contrib.git.utils import is_git_request
from projector.contrib.git.utils import get_wsgi_response
from projector.views.project import ProjectView

from vcs.web.simplevcs.utils import log_error


class ProjectGitBaseView(ProjectView):

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

    def response(self, request, username, project_slug):
        try:
            auth_response = self.get_authed_user()
            if auth_response:
                return auth_response
            git_server = GitWebServer(self.project.repository)
            response = git_server.get_response(request)
        except Exception, err:
            log_error(err)
            raise err
        return response

    def get_authed_user(self):
        if self.project.is_public():
            return None
        from vcs.web.simplevcs.utils import ask_basic_auth, basic_auth
        # Check if user have been already authorized or ask to
        self.request.user = basic_auth(self.request)
        if self.request.user is None:
            return ask_basic_auth(self.request,
                realm=self.project.config.basic_realm)



class GitWebServer(object):

    def __init__(self, repository):
        self.repository = repository
        self.response = HttpResponse()

    def get_response(self, request):
        #backend = DictBackend({'/': Repo(self.repository.path)})
        backend = ProjectorGitBackend(self.repository)
        app = GitApplication(backend)
        return get_wsgi_response(app, request)


class ProjectorHTTPGitRequest(HTTPGitRequest):

    def respond(self, *args, **kwargs):
        response = super(ProjectorHTTPGitRequest, self).respond(*args, **kwargs)
        return response


class GitApplication(HTTPGitApplication):

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        method = environ['REQUEST_METHOD']
        req = ProjectorHTTPGitRequest(environ, start_response, dumb=self.dumb,
                             handlers=self.handlers)
        # environ['QUERY_STRING'] has qs args
        handler = None
        for smethod, spath in self.services.iterkeys():
            if smethod != method:
                continue
            mat = spath.search(path)
            if mat:
                handler = self.services[smethod, spath]
                break
        if handler is None:
            logging.debug('Sorry, that method is not supported')
            raise Http404
            #return req.not_found('Sorry, that method is not supported')
        return handler(req, self.backend, mat)


class ProjectorGitBackend(Backend):

    def __init__(self, repository):
        self.repository = repository

    def open_repository(self, path):
        """
        Ignores path argument and returns dulwich repository.
        """
        return self.repository._repo._repo

