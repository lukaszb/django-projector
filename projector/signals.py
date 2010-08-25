import django.dispatch

post_fork = django.dispatch.Signal(providing_args=['fork'])

setup_project = django.dispatch.Signal(
    providing_args=['instance', 'vcs_alias', 'workflow'])

