from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.

# Validators


# def room_is_full(players):
#     if Room.player. > 3:
#         raise ValidationError('Room limit reached!')


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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
        return f'{self.category} | {self.value} | {self.date} | {self.text}'

#
# class Room(models.Model):
#     players = models.ForeignKey(Player, validators=[room_is_full()])