from django.db.models import signals

from projector import models as projector_app
from projector.management.listeners import put_missing_project_configs,\
    update_project_permissions, create_missing_repositories

signals.post_syncdb.connect(put_missing_project_configs, sender=projector_app,
    dispatch_uid='projector.management.put_missing_project_configs')

signals.post_syncdb.connect(update_project_permissions, sender=projector_app,
    dispatch_uid='projector.management.update_project_permissions')

signals.post_syncdb.connect(create_missing_repositories, sender=projector_app,
    dispatch_uid='projector.management.create_missing_repositories')

