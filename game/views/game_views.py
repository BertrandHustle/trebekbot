from random import choice

from django.conf import settings
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from game.models.Player import Player
from game.models.Question import Question
from game.serializers import QuestionSerializer
from util.judge import Judge


# TODO: unit test view
class QuestionView(APIView):

    def get(self, request):
        question = Question.get_random_question()
        # debug settings
        if settings.DEBUG:
            print(question.answer)
            print(f'Daily Double: {question.daily_double}')
            if settings.DAILY_DOUBLES_ONLY:
                question = Question.get_daily_double()
            elif settings.RANDOM_DAILY_DOUBLES:
                daily_double = choice([0, 1])
                question = Question.get_daily_double() if daily_double else Question.get_random_question()
            elif settings.VALID_LINKS_ONLY:
                question = Question.get_question_with_valid_links()
        serializer = QuestionSerializer(question)
        return Response(JSONRenderer().render(serializer.data))


class JudgeView(APIView):

    def __init__(self):
        self.judge = Judge()

    def post(self, request):
        """
        Answer a question and have player score updated accordingly
        :param request:
        :return: json with result of the answer (is the answer right or wrong?)
        """
        user = request.user
        user_answer = request.data.get('userAnswer')
        wager = request.data.get('wager')
        question = Question.objects.get(id=request.data.get('questionId'))
        judging_result = self.judge.judge_answer(user_answer, question.answer)
        question_value = wager if question.daily_double else question.value
        answer_result = {'result': '', 'text': '', 'score': 0}
        if judging_result == 'close':
            answer_result['text'] = self.judge.check_closeness(user_answer, question.answer)
        elif judging_result is True:
            answer_result['text'] = f'That is correct. The answer is "{question.answer}"'
            answer_result['result'] = True
            user.score += question_value
            user.save()
        elif judging_result is False:
            answer_result['text'] = f'Sorry, "{user_answer}" is incorrect.'
            answer_result['result'] = False
            user.score -= question_value
            user.save()
        answer_result['score'] = user.score
        return Response(answer_result)


class ScoreViewSet(viewsets.ViewSet):

    def get_user_score(self, request) -> Response:
        """
        get score of the current user
        """
        return Response(request.user.score)

    def get_top_ten(self, request) -> Response:
        """
        return a list of the top ten players by score
        """
        top_ten = Player.objects.order_by('-score')[:10]
        top_ten_dict = {player.username: player.score for player in top_ten}
        return Response(top_ten_dict)
