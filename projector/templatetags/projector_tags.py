import re

from django.conf import settings
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django import template
from django.utils.translation import ugettext as _

from projector.models import Task
from projector.models import get_user_from_string
from projector.settings import get_config_value
from projector.utils.email import EMAIL_RE

register = template.Library()

def restructuredtext(value):
    try:
        from docutils.core import publish_parts
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError("Error in {% restructuredtext %}"
                "filter: The Python docutils library isn't installed.")
        return force_unicode(value)
    else:
        docutils_settings = getattr(settings,
            "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        parts = publish_parts(source=smart_str(value), writer_name="html4css1",
            settings_overrides=docutils_settings)
        return mark_safe(force_unicode(parts["fragment"]))

@register.filter
def hide_email(value, sub=None):
    """
    Hide all emails founded within given value and replace them with given
    ``sub``stitution. If no ``sub`` is given,
    :setting:`PROJECTOR_HIDDEN_EMAIL_SUBSTITUTION` would be used.
    """
    if sub is None:
        sub = get_config_value('HIDDEN_EMAIL_SUBSTITUTION')
    value = EMAIL_RE.sub(sub, value)
    return value

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
        #import pdb; pdb.set_trace()
        value = re.sub(r'#(\d+)', repl, value)
    if path:
        raise NotImplementedError
    return mark_safe(value)

class FetchUserNode(template.Node):
    def __init__(self, value, context_var, get_from_context):
        self.value = value
        self.context_var = context_var
        self.get_from_context = get_from_context

    def render(self, context):
        if self.get_from_context:
            try:
                var = template.Variable(self.value).resolve(context)
            except template.VariableDoesNotExist:
                raise template.TemplateSyntaxError("Cannot resolve %s from "
                    "context" % self.value)
            user = get_user_from_string(var)
        else:
            user = get_user_from_string(self.value)
        context[self.context_var] = user
        return ''

@register.tag(name='fetch_user')
def do_fetch_user(parser, token):
    """
    Parses ``fetch_user`` tag which should be in format:
    {% fetch_user RAWID as "context_var" %}
    """
    format = '{% fetch_user RAWID as "context_var" %}'
    bits = token.split_contents()
    error_msg = "fetch_user tag should be in format: %s" % format
    if len(bits) == 4:
        if bits[2] != 'as':
            raise template.TemplateSyntaxError(error_msg)
        if bits[3][0] not in ['"', "'"] or bits[3][0] != bits[3][-1]:
            raise template.TemplateSyntaxError(error_msg)
        context_var = bits[3][1:-1]
        value = bits[1]
        if value[0] in '"\'' and value[0] == value[-1]:
            value = value.strip('"\'')
            get_from_context = False
        else:
            get_from_context = True
        return FetchUserNode(value, context_var, get_from_context)
    raise template.TemplateSyntaxError(error_msg)

