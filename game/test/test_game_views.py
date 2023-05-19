import json

import testing.postgresql

from django.test import RequestFactory, TestCase
from django.urls import reverse

from .fixtures import test_questions
from game.models.Player import Player
from game.models.Question import Question
from game.views.game_views import JudgeView, QuestionView


class GameViewTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        # set up test postgres db
        self.postgresql = testing.postgresql.Postgresql()

        # set up test user
        self.test_user = Player(name='Test Player')

    def tearDown(self):
        self.postgresql.stop()

    def test_judge_view(self):
        assert self.test_user.score == 0
        self.test_question = Question.get_random_question()
        redis_handler.set_active_question(self.test_question.to_json())

        request = self.factory.post(reverse('judge'), {'userAnswer': self.test_question.answer})
        request.user = self.test_user

        response = JudgeView.as_view()(request)
        json_response = json.loads(response.content)

        assert json_response['result'] is True
        assert self.test_user.score == self.test_question.value

    def test_question_view(self):
        request = self.factory.get(reverse('question'))
        request.user = self.test_user
        response = QuestionView.as_view()(request)
        json_response = json.loads(response.content)
        test_question = Question(json_response)
        assert test_question
        active_question = Question(json.loads(redis_handler.get_active_question()))
        assert active_question.question == test_question.question
        assert active_question.value == test_question.value
        assert active_question.air_date == test_question.air_date
