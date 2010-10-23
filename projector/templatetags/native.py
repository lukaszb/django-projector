from django.template.loader import render_to_string
from django.http import Http404

from projector.models import Membership, Watchable
from vcs.utils.annotate import annotate_highlight
from vcs.exceptions import VCSError
from native_tags.decorators import function, filter

def get_project_permissions(project=None, for_bit=None, user=None):
    """
    Usage::

       {% get_project_permissions PROJECT for USER [as "my_var"] %}

    Example::

       {% get_project_permissions project for request.user as "user_permissions" %}
    """
    assert project and for_bit == "for" and user
    try:
        return Membership.objects.get(project=project, member=user).all_perms
    except Membership.DoesNotExist:
        return []
get_project_permissions.function = True

def put_username_into_url(value, user):
    """
    Puts username into url for the given User object.
    ``value`` is first splitted and if any chunk starts with one of the prefixes
    defined below, username would be injected there.
    """
    if not user.is_authenticated():
        return value
    prefixes = ['http://', 'https://', 'ftp://']
    replacers = {}
    for chunk in value.split():
        for prefix in prefixes:
            if chunk.lower().startswith(prefix):
                newchunk = ''.join((
                    chunk[:len(prefix)],
                    user.username,
                    '@',
                    chunk[len(prefix):]))
                replacers[chunk] = newchunk
                break
    for chunk, replacer in replacers.items():
        value = value.replace(chunk, replacer, 1)
    return value
put_username_into_url = filter(put_username_into_url)

def is_watched(watchable, by_bit=None, user=None):
    """
    Usage::

       {% is_watched WATCHABLE by USER [as "my_var"] %}

    Provided context contains ``task`` and ``user`` objects we can use it as
    follows::

       {% is_watched task by user %}
    """
    assert watchable and isinstance(watchable, Watchable)
    assert by_bit == 'by'
    assert user
    return watchable.is_watched(user)
is_watched.function = True

def annotate_content(context, filenode, **options):
    """
    Usage::

       {% annotate_content filenode cssclass="code-highlight" %}
    """
    def annotate_changeset(changeset):
        template_name = "projector/project/repository/"\
                        "annotate_changeset_cell.html"

        context['line_changeset'] = changeset
        out = render_to_string(template_name, context)
        return out

    order = ['annotate', 'ls', 'code']
    headers = {}
    try:
        return annotate_highlight(filenode, order=order, headers=headers,
            annotate_from_changeset_func=annotate_changeset, **options)
    except VCSError:
        raise Http404
annotate_content = function(annotate_content, is_safe=True, takes_context=True)

