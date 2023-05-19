import json

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from game.models.Question import Question
from game.serializers import QuestionSerializer
from util.judge import Judge


# TODO: unit test view
class QuestionView(APIView):
    def get(self, request):
        question = Question.get_random_question()
        serializer = QuestionSerializer(question)
        return Response(JSONRenderer().render(serializer.data))


# TODO: remove this exemption!!!
@method_decorator(csrf_exempt, name='dispatch')
class JudgeView(APIView):

    def __init__(self):
        self.judge = Judge()
        self.response_templates = {
            'correct': 'That is correct. The answer is ',
            'incorrect': 'Sorry, that is incorrect.'
        }

    def post(self, request):
        """
        Answer a question and have player score updated accordingly
        :param request:
        :return: json with result of the answer (is the answer right or wrong?)
        """
        user = request.user
        user_answer = request.data.get('userAnswer')
        question = Question.objects.get(id=request.data.get('questionId'))
        judging_result = self.judge.judge_answer(user_answer, question.answer)
        question_value = question.value
        answer_result = {'result': '', 'text': '', 'score': 0}
        if judging_result == 'close':
            answer_result['text'] = self.judge.check_closeness(user_answer, question.answer)
        elif judging_result is True:
            answer_result['text'] = self.response_templates['correct'] + question.answer
            answer_result['result'] = True
            user.score += question_value
            user.save()
        elif judging_result is False:
            answer_result['text'] = self.response_templates['incorrect']
            answer_result['result'] = False
            user.score -= question_value
            user.save()
        answer_result['score'] = user.score
        return Response(answer_result)

