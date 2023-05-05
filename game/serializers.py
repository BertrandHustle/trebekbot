from rest_framework import serializers

from game.models import Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

    def create(self, validated_data):
        validated_data['value'] = Question.convert_value_to_int(validated_data['value'])
        return Question(**validated_data)
