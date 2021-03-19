from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import Question

from random import randint

from src.judge import Judge

# Create your views here.


def index(request):
    return HttpResponse("Welcome to Trebekbot 2.0!")


def play(request):
    return HttpResponse("play")


def judge_answer(request):
    if request.method == 'POST':
        answer_checker = Judge()
        given_answer = request.POST.get('givenAnswer')
        correct_answer = request.POST.get('correctAnswer')
        answer_result = {'result': ''}
        answer_is_correct = answer_checker.fuzz_answer(given_answer, correct_answer)
        if answer_is_correct == 'close':
            answer_result['result'] = answer_checker.check_closeness(given_answer, correct_answer)
        elif answer_is_correct:
            answer_result['result'] = 'That is correct. The answer is ' + given_answer
        elif not answer_is_correct:
            answer_result['result'] = 'Sorry, that is incorrect.'
        return JsonResponse(answer_result)


def new_question(request):
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
    return JsonResponse(question_json)