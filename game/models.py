from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

ROOM_LIMIT = 3

# Validators


# def room_is_full(players):
#     if len(players) > ROOM_LIMIT:
#         raise ValidationError('Room limit reached!')

# Models


class Player(AbstractUser):
    score = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)

    def __str__(self):
        return self.username

    # @receiver(post_save, sender=User)
    # def create_user_profile(self, sender, instance, created, **kwargs):
    #     if created:
    #         self.objects.create(user=instance)
    #
    # @receiver(post_save, sender=User)
    # def save_user_profile(self, sender, instance, **kwargs):
    #     instance.profile.save()


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


# class Room(models.Model):
#     players = models.ForeignKey(Player, validators=[room_is_full()])