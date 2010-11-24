import logging

from django.contrib import admin
from django.utils.translation import ugettext as _

from guardian.admin import GuardedModelAdmin

from projector.models import Component
from projector.models import Membership
from projector.models import Milestone
from projector.models import Priority
from projector.models import Project
from projector.models import ProjectCategory
from projector.models import Status
from projector.models import Task
from projector.models import TaskType
from projector.models import TaskRevision
from projector.models import Team

from richtemplates.forms import LimitingModelForm

from django_extensions.admin import ForeignKeyAutocompleteAdmin

def author_editor_save_model(self, request, obj, form, change):
    """
    Overrides standard admin.ModelAdmin save_model method.
    It sets editor (and his/her IP) based on data from requet.
    If model is new (it's primary key is not yet set) sets
    author/author_ip fields too.
    """

    logging.debug("%s.save_model method called!" % self.__class__.__name__)

    if getattr(obj, 'pk', None) is None:
        # Its a new instance so we need to
        # set author and author_ip fields
        obj.author = request.user
        obj.author_ip = request.META.get('REMOTE_ADDR', '')
    obj.editor = request.user
    obj.editor_ip = request.META.get('REMOTE_ADDR', '')

    return super(self.__class__, self).save_model(request, obj, form, change)

class StatusAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'name', 'order', 'is_resolved', 'project')
    list_display_links = ('id',)
    list_editable = ( 'name', 'order', 'is_resolved', )
    list_filter = ('project',)
    readonly_fields = ['project']

class TaskAdminForm(LimitingModelForm):
    class Meta:
        choices_limiting_fields = ['project']
        model = Task

class TaskRevisionInline(admin.TabularInline):
    model = TaskRevision
    extra = 1

class TaskAdmin(admin.ModelAdmin):
    list_display = ( 'project', 'component', 'id', 'summary',
        'created_at', 'author', 'status', 'priority', 'type')
    list_display_links = ('summary',)
    list_filter = ('project',)
    date_hierarchy = 'created_at'
    save_on_top = True
    search_fields = ['id', 'summary', 'description']
    form = TaskAdminForm

    fieldsets = (
        (_("Task detail"), {
            'fields': (
                'summary',
                ('project', 'component'),
                'description',
                'status',
                'priority',
                'type',
                'owner',
                'milestone',
                'deadline',
            )
        }),
        (_("Author & editor"), {
            'classes': ['collapsed collapse-toggle'],
            'fields': (
                ('author', 'author_ip'),
                ('editor', 'editor_ip'),
            ),
        }),
    )

    # This option would be used from Django 1.2
    readonly_fields = ('author_ip', 'editor_ip')

    class Media:
        css = {
            'all': ['projector/css/monoarea.css'],
        }

class TaskAutocompleteAdmin(TaskAdmin, ForeignKeyAutocompleteAdmin):
    related_search_fields = {
        'owner': ('username',),
    }

class OrderedDictModelAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'name', 'order', 'description' )
    list_display_links = ( 'id', 'name' )
    list_editable = ( 'order', )

class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 1

class TaskTypeInline(admin.TabularInline):
    model = TaskType
    extra = 1

class ComponentInline(admin.TabularInline):
    model = Component
    extra = 1

class StatusInline(admin.TabularInline):
    model = Status
    extra = 1

class PriorityInline(admin.TabularInline):
    model = Priority
    extra = 1

class ProjectAdmin(GuardedModelAdmin):
    list_display = ('id', 'name', 'category', 'home_page_url', 'is_active',
        'public', 'author', 'created_at', 'outdated')
    list_display_links = ('name',)
    list_filter = ('category', 'is_active', 'public', 'outdated')
    save_on_top = True
    search_fields = ['name', 'description']

    inlines = [MilestoneInline, ComponentInline, TaskTypeInline,
        StatusInline, PriorityInline]

    actions = ['make_public', 'make_private']

    def make_public(self, request, queryset):
        queryset.update(public=True)
    make_public.short_description = _("Make all selected projects public")

    def make_private(self, request, queryset):
        queryset.update(public=False)
    make_private.short_description = _("Make all selected projects private")

class ComponentAdmin(admin.ModelAdmin):
    list_display = 'project', 'name', 'description'
    list_display_links = 'name',
    list_filter = 'project',
    search_fields = ['project', 'name']


class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'name', 'order']
    list_display_links = ['name']
    list_filter = ['project']
    search_field = ['name', 'project']


admin.site.register(Status, StatusAdmin)
#admin.site.register(Priority, OrderedDictModelAdmin)
admin.site.register(TaskType, TaskTypeAdmin)
admin.site.register(Task, TaskAutocompleteAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectCategory)
admin.site.register(Membership)
admin.site.register(Team)
#admin.site.register(Component)
#admin.site.register(Milestone) # Should be maintain with project itself

