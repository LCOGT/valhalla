from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution = models.CharField(max_length=200)
    title = models.CharField(max_length=200)

    def __str__(self):
        return '{0} {1} at {2}'.format(self.user, self.title, self.institution)
