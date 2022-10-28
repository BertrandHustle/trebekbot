import json

from django.http import HttpResponse
from django.views import View

from src.question import Question


class QuestionView(View):
    def get(self, request):
        # transform Question attrs into dict
        return HttpResponse(json.dumps(Question.get_random_question()))
