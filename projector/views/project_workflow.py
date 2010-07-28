from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.db.models import Q

from projector.models import Status, Transition
from projector.views.project import ProjectView
from projector.forms import StatusForm, StatusFormSet

from richtemplates.shortcuts import get_first_or_None

class WorkflowDetailView(ProjectView):
    """
    Returns project's workflow detail view.
    """

    template_name = 'projector/project/workflow/detail.html'

    def response(self, request, username, project_slug):
        context = {
            'project': self.project,
            # indicates that this is workflow detail page at templates
            'workflow': True,
        }
        return context

class WorkflowEditView(ProjectView):
    """
    Edits chosen project's workflow.
    """

    template_name = 'projector/project/workflow/edit.html'
    perms = ['view_project', 'change_project']

    def response(self, request, username, project_slug):
        formset = StatusFormSet(request.POST or None,
            queryset=Status.objects.filter(project=self.project))
        if request.method == 'POST':
            if formset.is_valid():
                msg = _("Workflow updated successfully")
                messages.success(request, msg)
                for form in formset.forms:
                    # update status instance
                    form.instance.save()
                    destinations = form.cleaned_data['destinations']
                    # remove unchecked
                    Transition.objects.filter(~Q(destination__in=destinations),
                        source=form.instance)\
                        .delete()
                    # add new
                    for destination in destinations:
                        Transition.objects.get_or_create(source=form.instance,
                            destination=destination)
            else:
                msg = _("Errors occured while processing formset")
                messages.error(request, msg)
                for error in formset.non_form_errors():
                    messages.error(request, error)
        context = {
            'project': self.project,
            'formset': formset,
        }
        return context

class WorkflowAddStatusView(ProjectView):
    """
    Adds status for project's workflow.
    """

    template_name = 'projector/project/workflow/add_status.html'
    perms = ['view_project']

    def response(self, request, username, project_slug):
        _max_order_status = get_first_or_None(
            self.project.status_set.only('order').order_by('-order'))
        status = Status(project=self.project,
            order=_max_order_status and _max_order_status.order+1 or 1)
        form = StatusForm(request.POST or None, instance=status)
        if request.method == 'POST' and form.is_valid():
            form.save()
            msg = _("Status added successfully")
            messages.success(request, msg)
            return redirect(self.project.get_workflow_url())
        context = {
            'project': self.project,
            'form': form,
        }
        return context

