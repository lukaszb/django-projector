import django.dispatch

messanger = django.dispatch.Signal(providing_args=[
    'subject', 'body', 'from_address', 'recipient_list'])

post_fork = django.dispatch.Signal(providing_args=['fork'])

