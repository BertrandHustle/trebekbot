from os import path, pardir

from django.db import models
from django.contrib.auth.models import AbstractUser

project_root = path.join(path.dirname(path.abspath(__file__)), pardir)


class Player(AbstractUser):
    score = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)

    def __str__(self):
        return self.username
