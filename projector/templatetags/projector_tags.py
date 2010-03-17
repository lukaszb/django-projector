import re
import logging

from django.conf import settings
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django import template
from django.utils.translation import ugettext as _

from projector.models import Task

register = template.Library()

def restructuredtext(value):
    try:
        from docutils.core import publish_parts
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError("Error in {% restructuredtext %} filter: The Python docutils library isn't installed.")
        return force_unicode(value)
    else:
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=smart_str(value), writer_name="html4css1", settings_overrides=docutils_settings)
        return mark_safe(force_unicode(parts["fragment"]))

@register.filter
def changeset_message(value, project=None, path=None):
    if (project is None and path is None) or (project and path):
        raise template.TemplateSyntaxError, "Using changeset_message filter "\
            "without (or with both) ``project`` and ``path`` is not allowed. "\
            "You have to exactly one of them"
    value = escape(value)
    if project:
        def repl(m):
            id = int(m.group(1))
            try:
                task = project.get_task(id)
                message = _("Summary") + ": %s" % task.summary + "\n" + \
                    _("Status") + ": %s" % task.status
                archon = '<a href="%s" class="show-tipsy" title="%s">#%d</a>'\
                    % (task.get_absolute_url(), escape(message), id)
                if task.status.is_resolved:
                    archon = '<strike>' + archon + '</strike>'
            except Task.DoesNotExist:
                notask_message = _("There is no such task for this project")
                archon = '<span class="show-tipsy" title="%s">#%d</span>'\
                    % (notask_message, id)
            return archon
        value = re.sub(r'#(\d+)', repl, value)
    if path:
        raise NotImplementedError
    return mark_safe(value)

