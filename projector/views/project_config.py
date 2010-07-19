from django.utils.translation import ugettext as _
from django.shortcuts import redirect
from django.contrib import messages

from projector.views.project import ProjectView
from projector.forms import ConfigForm

class ConfigEditView(ProjectView):

    template_name = 'projector/project/config/home.html'

    def set_permissions(self):
        super(ConfigEditView, self).set_permissions()
        self.perms = ['view_project', 'change_config_project']

    def response(self, request, username, project_slug):
        config = self.project.config
        form = ConfigForm(request.POST or None, instance=config)
        if request.method == 'POST':
            if form.is_valid():
                form.instance.editor = request.user
                form.save()
                msg = _("Project's configuration updated successfully")
                messages.success(request, msg)
                return redirect(form.instance.project.get_absolute_url())
            else:
                msg = _("Errors occured while trying to update project's "
                    "configuration")
                messages.error(request, msg)
        context = {
            'project': self.project,
            'form': form,
        }
        return context

