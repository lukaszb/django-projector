import logging

from django.contrib import admin
from django.utils.translation import ugettext as _

from projector.models import Status, Task, Priority,\
    Project, ProjectCategory, TaskType, Milestone, ProjectComponent,\
    TaskRevision
from projector.models import Membership

from richtemplates.forms import LimitingModelForm
from attachments.admin import AttachmentInlines

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
        obj.author_ip = request.META['REMOTE_ADDR']
    obj.editor = request.user
    obj.editor_ip = request.META['REMOTE_ADDR']

    return super(self.__class__, self).save_model(request, obj, form, change)

class StatusAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'name', 'order', 'is_resolved', )
    list_display_links = ('id',)
    list_editable = ( 'name', 'order', 'is_resolved', )

class TaskAdminForm(LimitingModelForm):
    class Meta:
        choices_limiting_fields = ['project']
        model = Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ( 'pk', 'project', 'component', 'id', 'summary',
        'created_at', 'author', 'status', 'priority', 'type')
    list_display_links = ('summary',)
    list_filter = ('project', 'type', 'priority', 'status')
    date_hierarchy = 'created_at'
    save_on_top = True
    search_fields = ['summary', 'description']
    inlines = [AttachmentInlines]
    form = TaskAdminForm

    # Overrides save_model *method*
    '''
    def save_model(self, request, obj, form, change):
        """
        Overrides standard admin.ModelAdmin save_model method.
        It sets editor (and his/her IP) based on data from request.
        If model is new (it's primary key is not yet set) sets
        author/author_ip fields too.
        """

        logging.debug("%s.save_model method called!" % self.__class__.__name__)
        
        if getattr(obj, 'pk', None) is None:
            # Its a new instance so we need to
            # set author and author_ip fields
            obj.author = request.user
            obj.author_ip = request.META['REMOTE_ADDR']
        obj.editor = request.user
        obj.editor_ip = request.META['REMOTE_ADDR']
        #obj.save()
        return super(TaskAdmin, self).save_model(request, obj, form, change)
    '''

    fieldsets = (
        (_("Task details"), {
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
            'description': _("""This are readonly fields. In Django 1.2
                they will be probably really uneditable. For now, they are
                here but even if you change them, they will be overriden
                at the time of pushing data into database.""")
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

class TaskRevisionAdmin(admin.ModelAdmin):
    list_display = ( 'task', 'revision',
        'created_at', 'author', 'status', 'priority', 'type')
    #list_display_links = ('summary',)
    #list_filter = ('project', 'type', 'priority', 'status')
    date_hierarchy = 'created_at'
    save_on_top = True
    #search_fields = ['summary', 'description']

class OrderedDictModelAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'name', 'order', 'description' )
    list_display_links = ( 'id', 'name' )
    list_editable = ( 'order', )

class MilestoneInline(admin.StackedInline):
    model = Milestone
    extra = 1

class TaskTypeInline(admin.StackedInline):
    model = TaskType
    extra = 1

class ProjectComponentInline(admin.StackedInline):
    model = ProjectComponent 
    extra = 1

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'home_page_url', 'active',
        'public', 'author', 'created_at', 'outdated')
    list_display_links = ('name',)
    list_filter = ('category', 'active', 'public', 'outdated')
    save_on_top = True
    search_fields = ['name', 'description']    
    prepopulated_fields = {"slug": ("name",)}

    inlines = [MilestoneInline, ProjectComponentInline, TaskTypeInline]

class ProjectComponentAdmin(admin.ModelAdmin):
    list_display = 'project', 'name', 'description'
    list_display_links = 'name',
    list_filter = 'project',
    search_fields = ['project', 'name']


class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'name', 'order']
    list_display_links = ['name']
    list_filter = ['project']
    search_field = ['name', 'project']
    

#admin.site.register(Status, StatusAdmin)
#admin.site.register(Priority, OrderedDictModelAdmin)
admin.site.register(TaskType, TaskTypeAdmin)
admin.site.register(Task, TaskAutocompleteAdmin)
admin.site.register(TaskRevision, TaskRevisionAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectCategory)
admin.site.register(Membership)
#admin.site.register(ProjectComponent)
#admin.site.register(Milestone) # Should be maintain with project itself

