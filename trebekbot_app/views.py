# django
from django.http import HttpResponse
from .models import Question

# native
from random import randint


def question(request):
    # get random question
    question_count = Question.objects.count()
    rand_question = Question.objects.get(pk=randint(0, question_count))
    return HttpResponse(rand_question)


def test(request):
    return HttpResponse("Welcome to Trebekbot!")
