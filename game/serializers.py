from rest_framework import serializers

from game.models.Question import Question


class QuestionSerializer(serializers.ModelSerializer):

    text = serializers.CharField(source='question')

    class Meta:
        model = Question
        fields = '__all__'

    def create(self, validated_data):
        validated_data['value'] = Question.convert_value_to_int(validated_data['value'])
        return Question(**validated_data)
