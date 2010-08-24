import django.dispatch

mails = django.dispatch.Signal(providing_args=[
    'subject', 'message', 'from_email', 'recipient_list'])

post_fork = django.dispatch.Signal(providing_args=['fork'])

setup_project = django.dispatch.Signal(
    providing_args=['instance', 'vcs_alias', 'workflow'])

