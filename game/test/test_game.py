import json

import testing.postgresql
from fakeredis import FakeStrictRedis

from django.test import RequestFactory, TestCase
from django.urls import reverse

from src.question import Question

from game.models import Player
from game.views.game_views import redis_handler, JudgeView


class GameViewTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        # override redis connection w/fake
        redis_handler.redis_connection = FakeStrictRedis()

        # set up test postgres db
        postgresql = testing.postgresql.Postgresql()

        # set up test user
        self.test_user = Player(name='Test Player')

    def test_judge_view(self):
        self.test_question = Question.get_random_question()
        redis_handler.set_active_question(json.dumps(self.test_question.to_json()))

        request = self.factory.post(reverse('judge'), {'user_answer': self.test_question.answer})
        request.user = self.test_user

        response = JudgeView.as_view()(request)

        assert response['result'] is True
