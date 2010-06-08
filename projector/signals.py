import django.dispatch

messanger = django.dispatch.Signal(providing_args=[
    'subject', 'body', 'from_address', 'recipient_list'])

