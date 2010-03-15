import django_filters

from django import forms
from django.utils.translation import ugettext as _
from projector.models import Task

class ResolvedStatusFilter(django_filters.BooleanFilter):
    field_class = forms.NullBooleanField

    def __init__(self, *args, **kwargs):
        super(ResolvedStatusFilter, self).__init__(*args, **kwargs)
        self.field.widget.choices[0] = (u'1', _('All'))

    def filter(self, qs, value):
        if value is not None:
            return qs.filter(status__is_resolved=value)
        return qs

def TaskFilter(data=None, queryset=Task.objects.all(), project=None):
    """
    Factory method which returns ``FilterSet`` for given project.
    """
    class TaskFilter(django_filters.FilterSet):
        is_resolved = ResolvedStatusFilter()
        class Meta:
            model = Task
            fields = ['id', 'priority', 'milestone', 'status']

        def __init__(self, *args, **kwargs):
            super(TaskFilter, self).__init__(*args, **kwargs)
            if project:
                self.filters['status'].extra.update(
                    {'queryset': project.status_set.all()})
                self.filters['priority'].extra.update(
                    {'queryset': project.priority_set.all()})
                self.filters['milestone'].extra.update(
                    {'queryset': project.milestone_set.all()})
    filterset = TaskFilter(data, queryset)
    return filterset

