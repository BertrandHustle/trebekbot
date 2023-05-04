from rest_framework import serializers


class QuestionSerializer(serializers.ModelSerializer):
    text = serializers.CharField(max_length=750)
    value = serializers.IntegerField()
    category = serializers.CharField(max_length=100)
    daily_double = serializers.BooleanField()
    answer = serializers.CharField(max_length=250)
    valid_links = serializers.ListField(
        child=serializers.CharField(max_length=50, allow_blank=True),
    )
    air_date = serializers.DateField()
