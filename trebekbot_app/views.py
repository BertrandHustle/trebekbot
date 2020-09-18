# django
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from .models import Question

# native
from random import randint


def question(request):
    # get random question
    question_count = Question.objects.count()
    rand_question = Question.objects.get(pk=randint(0, question_count))
    question_json = {
        'text': rand_question.text,
        'valid_links': rand_question.valid_links,
        'value': rand_question.value,
        'category': rand_question.category,
        'daily_double': rand_question.daily_double,
        'answer': rand_question.answer,
        'date': rand_question.date
    }
    # data = serializers.serialize("json", [question_json, ])
    return render(request, 'trebekbot_app/question.html', {"question_json": question_json})


def test(request):
    return HttpResponse("Welcome to Trebekbot!")
