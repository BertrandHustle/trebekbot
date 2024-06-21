import json

import pytest

from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from game.test.fixtures import test_player, test_questions
from game.views.game_views import JudgeView, QuestionView


@pytest.mark.django_db
class TestGameViews:

    # TODO: make daily double test
    def test_judge_view(self, test_player, test_questions):
        assert test_player.score == 0
        test_question = test_questions['valid_question']
        request_body = {
            'questionId': test_question.id,
            'userAnswer': test_question.answer
        }
        request = APIRequestFactory().post(reverse('judge'), request_body)
        force_authenticate(request, user=test_player)
        response = JudgeView.as_view()(request)
        assert response.status_code == 200
        assert response.data['result'] is True
        assert test_player.score == test_question.value

    def test_get_question_view(self, test_player, test_questions):
        request = APIRequestFactory().get(reverse('question'))
        force_authenticate(request, user=test_player)
        response = QuestionView.as_view()(request)
        assert response.status_code == 200
        json_response = json.loads(response.data)
        assert json_response['text']
        assert json_response['category']
        assert json_response['air_date']

    def test_post_question_view(self, test_player, test_questions):
        test_question = test_questions['valid_question']
        request = APIRequestFactory().post(reverse('question'), {'questionId': test_question.id})
        force_authenticate(request, user=test_player)
        response = QuestionView.as_view()(request)
        assert response.status_code == 200
        json_response = json.loads(response.data)
        assert json_response['text'] == test_question.text
        assert json_response['category'] == test_question.category
        assert json_response['air_date'] == str(test_question.air_date)
