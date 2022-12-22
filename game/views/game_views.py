import json

from django.http import JsonResponse
from django.views import View

from src.question import Question
from src.judge import Judge
from src.redis_interface import RedisInterface

redis_handler = RedisInterface()


# TODO: unit test view
class QuestionView(View):
    def get(self, request):
        active_question_json = Question.get_random_question().to_json()
        redis_handler.set_active_question(active_question_json)
        # transform Question attrs into dict
        return JsonResponse(active_question_json)


class JudgeView(View):

    def __init__(self):
        self.judge = Judge()
        self.response_templates = {
            'correct': 'That is correct. The answer is ',
            'incorrect': 'Sorry, that is incorrect.'
        }

    def post(self, request):
        user = request.user
        user_answer = request.POST.get('user_answer')
        question_json = json.loads(redis_handler.get_active_question())
        question = Question(question_json)
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
        elif judging_result is not False:
            answer_result['text'] = self.response_templates['incorrect']
            answer_result['result'] = False
            user.score -= question_value
            user.save()
        answer_result['score'] = user.score
        return JsonResponse(answer_result)

