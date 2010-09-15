from django.views.generic import simple

def home(request, template_name='projector/home.html'):
    """
    Home view for projector app.
    """

    return simple.direct_to_template(request, {'template': template_name})

