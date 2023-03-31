from rest_framework import serializers
from .models import Player, Question


class PlayerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Player
        fields = ('user', 'username', 'score', 'wins')


#TODO: make question serializer