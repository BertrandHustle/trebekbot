# django
from django.db import models
# native
from json import loads as json_loads
from contextlib import suppress
# Create your models here.


class User(models.Model):
    name = models.CharField(max_length=50, unique=True)
    score = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Question(models.Model):
    text = models.CharField(max_length=750)
    value = models.IntegerField()
    category = models.CharField(max_length=100)
    daily_double = models.BooleanField(default=False)
    answer = models.CharField(max_length=250)
    date = models.CharField(max_length=50)
    valid_links = models.CharField(max_length=500, blank=True, default='')

    def __str__(self):
        return '{0}, {1}, {2}, {3}'.format(self.category, self.value, self.date, self.text)

