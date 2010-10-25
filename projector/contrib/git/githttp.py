import logging

from django.http import Http404, HttpResponse
from django.utils.translation import ugettext as _
from django.template.defaultfilters import filesizeformat

from dulwich.pack import write_pack_data
from dulwich.protocol import ProtocolFile
from dulwich.server import Backend
from dulwich.server import UploadPackHandler
from dulwich.server import ProtocolGraphWalker
from dulwich.web import HTTPGitApplication
from dulwich.web import HTTPGitRequest

from projector.contrib.git.utils import get_wsgi_response


class GitWebServer(object):

    class Type:
        READ = 'read'
        WRITE = 'write'
        UNSPECIFIED = 'unspecified'

    def __init__(self, repository):
        self.repository = repository
        self.response = HttpResponse()

    def get_response(self, request):
        backend = ProjectorGitBackend(self.repository)
        app = GitApplication(backend, handlers={
            'git-upload-pack': ProjectorUploadPackHandler,
        })
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


class ProjectorUploadPackHandler(UploadPackHandler):
    """
    handle method overridden in order to controll messages.
    """

    def handle(self):
        write = lambda x: self.proto.write_sideband(1, x)

        graph_walker = ProtocolGraphWalker(self, self.repo.object_store,
            self.repo.get_peeled)
        objects_iter = self.repo.fetch_objects(
          graph_walker.determine_wants, graph_walker, self.progress,
          get_tagged=self.get_tagged)

        # Do they want any objects?
        if len(objects_iter) == 0:
            return

        #self.progress("dul-daemon says what\n")
        self.progress("counting objects: %d, done.\n" % len(objects_iter))
        write_pack_data(ProtocolFile(None, write), objects_iter,
                        len(objects_iter))
        #self.progress("how was that, then?\n")
        size = self.backend.repository.info.size
        msg = _('Repository size: %s\n' % filesizeformat(size))
        logging.info(msg)
        self.progress(msg)
        # we are done
        self.proto.write("0000")

