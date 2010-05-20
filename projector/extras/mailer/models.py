from django.db import models

class Message(models.Model):
    subject = models.CharField(max_length=512)
    body = models.TextField()
    from_address = models.EmailField()
    recipient_list = models.TextField()

    def __unicode__(self):
        pass
