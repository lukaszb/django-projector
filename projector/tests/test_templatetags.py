from django.test import TestCase
from django.template import Template, Context

from projector.settings import get_config_value

def render(template, context):
    """
    Returns rendered ``template`` with ``context``, which are given as string
    and dict respectively.
    """
    t = Template(template)
    return t.render(Context(context))


class HideEmailTest(TestCase):
    """
    Tests against hide_email filter.
    """

    def setUp(self):
        self.sub = get_config_value('HIDDEN_EMAIL_SUBSTITUTION')

    def test_simple(self):

        template = ''.join((
            '{% load projector_tags %}',
            '{{ author|hide_email }}',
        ))
        context = {'author': 'Joe Doe [joe.doe@example.com]'}
        output = render(template, context)

        self.assertEqual(output, 'Joe Doe [%s]' % (self.sub))

    def test_with_parameter(self):

        template = ''.join((
            '{% load projector_tags %}',
            '{{ author|hide_email:"HIDDEN_EMAIL" }}',
        ))
        context = {'author': 'Joe Doe [joe.doe@example.com]'}
        output = render(template, context)

        self.assertEqual(output, 'Joe Doe [%s]' % ('HIDDEN_EMAIL'))

    def test_multiple_simple(self):

        template = ''.join((
            '{% load projector_tags %}',
            '{% for author in authors %}'
            '{{ author|hide_email }}\n',
            '{% endfor %}',
        ))
        authors = ['Joe Doe [joe.doe@example.com]', 'Jack (jack@example.com)']
        context = {'authors': authors}
        output = render(template, context)

        self.assertEqual(output,
            'Joe Doe [%(sub)s]\n'
            'Jack (%(sub)s)\n' % {'sub': self.sub})

    def test_multiple_with_parameter(self):

        template = ''.join((
            '{% load projector_tags %}',
            '{% for author in authors %}'
            '{{ author|hide_email:"HIDDEN_EMAIL" }}\n',
            '{% endfor %}',
        ))
        authors = ['Joe Doe [joe.doe@example.com]', 'Jack (jack@example.com)']
        context = {'authors': authors}
        output = render(template, context)

        self.assertEqual(output,
            'Joe Doe [%(sub)s]\n'
            'Jack (%(sub)s)\n' % {'sub': 'HIDDEN_EMAIL'})

