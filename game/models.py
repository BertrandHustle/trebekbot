from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

ROOM_LIMIT = 3

# Validators


# def room_is_full(players):
#     if len(players) > ROOM_LIMIT:
#         raise ValidationError('Room limit reached!')

# Models


class Player(AbstractBaseUser):
    name = models.CharField(max_length=50, unique=True)
    score = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    password = ''

    # fields required by AbstractBaseUser
    REQUIRED_FIELDS = ['name']
    USERNAME_FIELD = 'name'


    def __str__(self):
        return self.name

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