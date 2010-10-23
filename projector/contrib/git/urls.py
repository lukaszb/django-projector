from django.conf.urls.defaults import *

urlpatterns = patterns('projector.contrib.git.views',
    url(r'^$', 'ProjectGitHandler', name='projector-project-git'),
    url(r'^', 'ProjectGitHandler', name='projector-project-git-handler'),
)

