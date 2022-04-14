from django.apps import AppConfig


class GameConfig(AppConfig):
    name = 'game'

    # wipe scores on startup
    def ready(self):
        from .models import Player
        Player.objects.all().update(score=0)
