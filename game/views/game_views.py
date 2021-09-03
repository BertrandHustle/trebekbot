from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


from game.models import Question, Player

from random import randint

from src.judge import Judge
from src.redis_interface import RedisInterface

answer_checker = Judge()
redis_handler = RedisInterface()


def index(request):
    return HttpResponse("Welcome to Trebekbot 2.0!")


@login_required
def play(request):
    players = Player.objects.filter(name__in=redis_handler.get_all_players())
    return render(request, "game/play.html", {
        'players': players,
        'player_name': request.user.username,
        'player_score': request.user.player.score
    })


def judge_answer(request):
    if request.method == 'POST':
        player = Player.objects.get(user=request.user)
        given_answer = request.POST.get('givenAnswer')
        correct_answer = request.POST.get('correctAnswer')
        question_value = int(request.POST.get('questionValue'))
        answer_result = {'result': '', 'text': '', 'player_score': 0}
        answer_is_correct = answer_checker.fuzz_answer(given_answer, correct_answer)
        if answer_is_correct == 'close':
            answer_result['text'] = answer_checker.check_closeness(given_answer, correct_answer)
        elif answer_is_correct:
            answer_result['text'] = 'That is correct. The answer is ' + given_answer
            answer_result['result'] = True
            player.score += question_value
            player.save()
        elif not answer_is_correct:
            answer_result['text'] = 'Sorry, that is incorrect.'
            answer_result['result'] = False
            player.score -= question_value
            player.save()
        answer_result['player_score'] = player.score
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
    # DEBUG
    print(rand_question.answer)
    return JsonResponse(question_json)

