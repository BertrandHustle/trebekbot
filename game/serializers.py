from rest_framework import serializers
from .models import Player, Question

class PlayerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Player
        fields = ('user', 'name', 'score'. 'wins')
        