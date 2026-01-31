from django.db import models

from django.db import models

class Teams(models.Model):
    name = models.CharField(max_length=100, default="temp")

    def __str__(self):
        return self.name
