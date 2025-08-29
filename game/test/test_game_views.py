import json

import pytest

from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from game.models.Board import Board
from game.models.BoardUtils import BoardUtils
from game.models.QuestionTile import QuestionTile
from game.serializers import QuestionSerializer
from game.test.fixtures import test_board, test_categories, test_player, test_questions
from game.views.game_views import BoardView, JudgeView, QuestionView


@pytest.mark.django_db
class TestJudgeViews:

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


@pytest.mark.django_db
class TestQuestionViews:

    def test_get_question_view(self, test_player, test_questions):
        request = APIRequestFactory().get(reverse('question'))
        force_authenticate(request, user=test_player)
        response = QuestionView.as_view()(request)
        assert response.status_code == 200
        assert response.data['text']
        assert response.data['category']
        assert response.data['air_date']

    def test_post_question_view(self, test_player, test_questions):
        test_question = test_questions['valid_question']
        request = APIRequestFactory().post(reverse('question'), {'questionId': test_question.id})
        force_authenticate(request, user=test_player)
        response = QuestionView.as_view()(request)
        assert response.status_code == 200
        assert response.data['text'] == test_question.text
        assert response.data['category'] == test_question.category
        assert response.data['air_date'] == str(test_question.air_date)


@pytest.mark.django_db
class TestBoardViews:

    @pytest.mark.parametrize('test_categories', [None], indirect=['test_categories'])
    def test_new_board_view(self, test_categories, test_player):
        # arrange
        test_categories.create_test_categories()
        # act
        request = APIRequestFactory().post(reverse('board'), {'round': 'Jeopardy!'})
        force_authenticate(request, user=test_player)
        response = BoardView.as_view()(request)
        # assert
        assert response.status_code == 200
        board_id = response.data['boardId']
        test_board = Board.objects.get(id=board_id)
        assert len(test_board.questiontile_set.all()) == 30
        assert board_id == 1
        question_dict = response.data['boardDict']
        assert len(question_dict) == 6
        for category in question_dict:
            question_tiles = question_dict[category]
            assert len(question_tiles) == 5
            for question_json in question_tiles:
                question_serializer = QuestionSerializer(data=question_json['question'])
                question_serializer.is_valid(raise_exception=True)


    def test_existing_board_view(self, test_board, test_player):
        # act
        request = APIRequestFactory().get(reverse('board'), {'boardId': test_board.pk})
        force_authenticate(request, user=test_player)
        response = BoardView.as_view()(request)
        # assert
        assert response.status_code == 200
        expected_board_dict = BoardUtils.tiles_to_dict(test_board)
        expected_ids, test_ids = set(), set()
        for category, questions in expected_board_dict.items():
            expected_ids.update([q['id'] for q in questions])
        for category, questions in response.data['boardDict'].items():
            test_ids.update([q['id'] for q in questions])
        assert expected_ids == test_ids


    def test_non_existing_board_view(self, test_player):
        request = APIRequestFactory().get(reverse('board'), {'boardId': 0})
        force_authenticate(request, user=test_player)
        response = BoardView.as_view()(request)
        assert response.status_code == 404


    def test_patch_board_view(self, test_board, test_player):
        test_question_tile = QuestionTile.objects.first()
        assert test_question_tile.alive is True
        request = APIRequestFactory().patch(reverse('board'), {'questionTileId': test_question_tile.pk})
        force_authenticate(request, user=test_player)
        response = BoardView.as_view()(request)
        assert response.status_code == 200
        updated_question_tile = QuestionTile.objects.get(pk=test_question_tile.pk)
        assert updated_question_tile.alive is False
