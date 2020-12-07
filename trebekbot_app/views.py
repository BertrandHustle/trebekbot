# django
from django.http import JsonResponse
from django.shortcuts import render
from django.template import RequestContext, Template
from .models import Question

# native
from random import randint
from json import dumps as json_dumps

# project
from src.judge import Judge


def game(request):
    return render(request, 'trebekbot_app/game.html')


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
