# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'ProjectCategory'
        db.create_table('projector_projectcategory', (
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=64, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
        ))
        db.send_create_signal('projector', ['ProjectCategory'])

        # Adding model 'Project'
        db.create_table('projector_project', (
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.ProjectCategory'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('repository', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['simplevcs.Repository'], null=True, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_projects', to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('home_page_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('outdated', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
        ))
        db.send_create_signal('projector', ['Project'])

        # Adding model 'Component'
        db.create_table('projector_component', (
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique_with=(), max_length=64, populate_from=None, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('projector', ['Component'])

        # Adding unique constraint on 'Component', fields ['project', 'name']
        db.create_unique('projector_component', ['project_id', 'name'])

        # Adding model 'Membership'
        db.create_table('projector_membership', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('joined_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('projector', ['Membership'])

        # Adding unique constraint on 'Membership', fields ['project', 'member']
        db.create_unique('projector_membership', ['project_id', 'member_id'])

        # Adding model 'Team'
        db.create_table('projector_team', (
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('joined_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('projector', ['Team'])

        # Adding unique constraint on 'Team', fields ['project', 'group']
        db.create_unique('projector_team', ['project_id', 'group_id'])

        # Adding model 'UserProfile'
        db.create_table('projector_userprofile', (
            ('code_style', self.gf('django.db.models.fields.CharField')(default='native', max_length=128)),
            ('skin', self.gf('django.db.models.fields.CharField')(default='ruby', max_length=128)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('activation_token', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal('projector', ['UserProfile'])

        # Adding model 'Milestone'
        db.create_table('projector_milestone', (
            ('date_completed', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('deadline', self.gf('django.db.models.fields.DateField')(default=datetime.date(2010, 7, 11))),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique_with=(), max_length=64, populate_from=None, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('projector', ['Milestone'])

        # Adding model 'TimelineEntry'
        db.create_table('projector_timelineentry', (
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('projector', ['TimelineEntry'])

        # Adding model 'Priority'
        db.create_table('projector_priority', (
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique_with=(), max_length=64, populate_from=None, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('projector', ['Priority'])

        # Adding unique constraint on 'Priority', fields ['project', 'name']
        db.create_unique('projector_priority', ['project_id', 'name'])

        # Adding model 'Status'
        db.create_table('projector_status', (
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique_with=(), max_length=64, populate_from=None, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_resolved', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('is_initial', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('projector', ['Status'])

        # Adding unique constraint on 'Status', fields ['project', 'name']
        db.create_unique('projector_status', ['project_id', 'name'])

        # Adding model 'Transition'
        db.create_table('projector_transition', (
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sources', to=orm['projector.Status'])),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Status'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('projector', ['Transition'])

        # Adding unique constraint on 'Transition', fields ['source', 'destination']
        db.create_unique('projector_transition', ['source_id', 'destination_id'])

        # Adding model 'TaskType'
        db.create_table('projector_tasktype', (
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('projector', ['TaskType'])

        # Adding unique constraint on 'TaskType', fields ['project', 'name']
        db.create_unique('projector_tasktype', ['project_id', 'name'])

        # Adding model 'Task'
        db.create_table('projector_task', (
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Status'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Project'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_task', blank=True, to=orm['auth.User'])),
            ('edited_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id_pk', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Component'])),
            ('author_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, blank=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('priority', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Priority'])),
            ('editor_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, blank=True)),
            ('deadline', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('editor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Milestone'], null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owned_task', null=True, to=orm['auth.User'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.TaskType'])),
            ('id', self.gf('django.db.models.fields.IntegerField')()),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('projector', ['Task'])

        # Adding unique constraint on 'Task', fields ['id', 'project']
        db.create_unique('projector_task', ['id', 'project_id'])

        # Adding model 'TaskRevision'
        db.create_table('projector_taskrevision', (
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Status'])),
            ('comment', self.gf('django.db.models.fields.TextField')(max_length=3000, null=True, blank=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Task'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_taskrevision', blank=True, to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Component'])),
            ('author_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, blank=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('priority', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Priority'])),
            ('deadline', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('milestone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.Milestone'], null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owned_taskrevision', null=True, to=orm['auth.User'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['projector.TaskType'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('projector', ['TaskRevision'])

        # Adding unique constraint on 'TaskRevision', fields ['revision', 'task']
        db.create_unique('projector_taskrevision', ['revision', 'task_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'ProjectCategory'
        db.delete_table('projector_projectcategory')

        # Deleting model 'Project'
        db.delete_table('projector_project')

        # Deleting model 'Component'
        db.delete_table('projector_component')

        # Removing unique constraint on 'Component', fields ['project', 'name']
        db.delete_unique('projector_component', ['project_id', 'name'])

        # Deleting model 'Membership'
        db.delete_table('projector_membership')

        # Removing unique constraint on 'Membership', fields ['project', 'member']
        db.delete_unique('projector_membership', ['project_id', 'member_id'])

        # Deleting model 'Team'
        db.delete_table('projector_team')

        # Removing unique constraint on 'Team', fields ['project', 'group']
        db.delete_unique('projector_team', ['project_id', 'group_id'])

        # Deleting model 'UserProfile'
        db.delete_table('projector_userprofile')

        # Deleting model 'Milestone'
        db.delete_table('projector_milestone')

        # Deleting model 'TimelineEntry'
        db.delete_table('projector_timelineentry')

        # Deleting model 'Priority'
        db.delete_table('projector_priority')

        # Removing unique constraint on 'Priority', fields ['project', 'name']
        db.delete_unique('projector_priority', ['project_id', 'name'])

        # Deleting model 'Status'
        db.delete_table('projector_status')

        # Removing unique constraint on 'Status', fields ['project', 'name']
        db.delete_unique('projector_status', ['project_id', 'name'])

        # Deleting model 'Transition'
        db.delete_table('projector_transition')

        # Removing unique constraint on 'Transition', fields ['source', 'destination']
        db.delete_unique('projector_transition', ['source_id', 'destination_id'])

        # Deleting model 'TaskType'
        db.delete_table('projector_tasktype')

        # Removing unique constraint on 'TaskType', fields ['project', 'name']
        db.delete_unique('projector_tasktype', ['project_id', 'name'])

        # Deleting model 'Task'
        db.delete_table('projector_task')

        # Removing unique constraint on 'Task', fields ['id', 'project']
        db.delete_unique('projector_task', ['id', 'project_id'])

        # Deleting model 'TaskRevision'
        db.delete_table('projector_taskrevision')

        # Removing unique constraint on 'TaskRevision', fields ['revision', 'task']
        db.delete_unique('projector_taskrevision', ['revision', 'task_id'])
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'projector.component': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Component'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '64', 'populate_from': 'None', 'db_index': 'True'})
        },
        'projector.membership': {
            'Meta': {'unique_together': "(('project', 'member'),)", 'object_name': 'Membership'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'joined_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"})
        },
        'projector.milestone': {
            'Meta': {'object_name': 'Milestone'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_completed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'deadline': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2010, 7, 11)'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '64', 'populate_from': 'None', 'db_index': 'True'})
        },
        'projector.priority': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Priority'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '64', 'populate_from': 'None', 'db_index': 'True'})
        },
        'projector.project': {
            'Meta': {'object_name': 'Project'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_projects'", 'to': "orm['auth.User']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.ProjectCategory']", 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'home_page_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'through': "orm['projector.Membership']", 'symmetrical': 'False'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'outdated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'repository': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['simplevcs.Repository']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'teams': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Group']", 'null': 'True', 'through': "orm['projector.Team']", 'blank': 'True'})
        },
        'projector.projectcategory': {
            'Meta': {'object_name': 'ProjectCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'})
        },
        'projector.status': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Status'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'destinations': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['projector.Status']", 'null': 'True', 'through': "orm['projector.Transition']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_initial': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_resolved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique_with': '()', 'max_length': '64', 'populate_from': 'None', 'db_index': 'True'})
        },
        'projector.task': {
            'Meta': {'unique_together': "(('id', 'project'),)", 'object_name': 'Task'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_task'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'author_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'blank': 'True'}),
            'component': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Component']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'deadline': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'edited_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'editor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'editor_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'blank': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {}),
            'id_pk': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Milestone']", 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_task'", 'null': 'True', 'to': "orm['auth.User']"}),
            'priority': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Priority']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Status']"}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.TaskType']"})
        },
        'projector.taskrevision': {
            'Meta': {'unique_together': "(('revision', 'task'),)", 'object_name': 'TaskRevision'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_taskrevision'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'author_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '3000', 'null': 'True', 'blank': 'True'}),
            'component': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Component']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'deadline': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Milestone']", 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_taskrevision'", 'null': 'True', 'to': "orm['auth.User']"}),
            'priority': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Priority']"}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Status']"}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Task']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.TaskType']"})
        },
        'projector.tasktype': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'TaskType'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"})
        },
        'projector.team': {
            'Meta': {'unique_together': "(('project', 'group'),)", 'object_name': 'Team'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'joined_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"})
        },
        'projector.timelineentry': {
            'Meta': {'object_name': 'TimelineEntry'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'projector.transition': {
            'Meta': {'unique_together': "(('source', 'destination'),)", 'object_name': 'Transition'},
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projector.Status']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sources'", 'to': "orm['projector.Status']"})
        },
        'projector.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'activation_token': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'code_style': ('django.db.models.fields.CharField', [], {'default': "'native'", 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'skin': ('django.db.models.fields.CharField', [], {'default': "'ruby'", 'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'simplevcs.repository': {
            'Meta': {'object_name': 'Repository'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }
    
    complete_apps = ['projector']
