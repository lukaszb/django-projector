import django_filters

from projector.models import Task

def TaskFilter(data=None, queryset=Task.objects.all(), project=None):
    """
    Factory method which returns ``FilterSet`` for given project.
    """
    class TaskFilter(django_filters.FilterSet):
        class Meta:
            model = Task
            fields = ['id', 'status', 'priority', 'milestone']

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

