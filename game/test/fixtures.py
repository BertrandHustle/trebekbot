import json
from datetime import datetime
from pathlib import Path

import pytest

from game.models.Board import Board
from game.models.BoardUtils import BoardUtils
from game.models.Player import Player
from game.models.Question import Question
from game.serializers import QuestionSerializer
from paths import ROOT_DIR


@pytest.fixture
def test_player():
    yield Player.objects.create(username='Test Player')


class GenericTestQuestionCreator:
    def __init__(self, num_questions: int, starting_value: int = 100):
        self.num_questions = num_questions
        self.starting_value = starting_value

    def create_generic_questions(self, num_questions: int, starting_value: int = None, value_list: list[int] = None):

        generic_question_data = {
            'text': 'test',
            'value': 0,
            'answer': 'test_answer',
            'category': 'Test Category',
            'air_date': '1999-09-09',
            'round': 'Jeopardy!',
            'valid_links': ['test.com']
        }

        if starting_value:
            value = starting_value
            for i in range(num_questions):
                new_question_data = generic_question_data.copy()
                new_question_data['value'] = value
                question_serializer = QuestionSerializer(data=new_question_data)
                question_serializer.is_valid(raise_exception=True)
                question_serializer.create(new_question_data).save()
                value += starting_value
        elif value_list:
            for value in value_list:
                new_question_data = generic_question_data.copy()
                new_question_data['value'] = value
                question_serializer = QuestionSerializer(data=new_question_data)
                question_serializer.is_valid(raise_exception=True)
                question_serializer.create(new_question_data).save()


@pytest.fixture
def generic_test_questions(request):
    return GenericTestQuestionCreator(request.param)

@pytest.fixture
def test_categories():
    for cat in range(6):
        if cat % 2 == 0:
            value_scaler = 100
        else:
            value_scaler = 200
        value = value_scaler
        for i in range(5):
            Question.objects.create(
                text='test',
                value=value,
                answer='test_answer',
                category=f'Category {cat}',
                air_date=datetime.now(),
                round='Jeopardy!',
                valid_links=['test.com']  # needed to satisfy serializer
            )
            value += value_scaler


@pytest.fixture
def test_board(test_categories):
    board = Board.objects.create()
    BoardUtils.fill_board(board, 'Jeopardy!')
    yield board


@pytest.fixture
def test_questions():
    question_json_path = Path(ROOT_DIR, 'game', 'test', 'test_files', 'test_questions.json')
    with open(question_json_path) as test_question_json_file:
        questions = {}
        question_json = json.load(test_question_json_file)
        for question_name, question in question_json.items():
            value = Question.convert_value_to_int(question['value'])
            text, valid_links = Question.separate_html(question['question'])
            test_question = Question(
                text=text,
                value=value,
                category=question['category'],
                daily_double=Question.is_daily_double(value),
                answer=question['answer'],
                air_date=datetime.strptime(question['air_date'], '%Y-%m-%d').date()
            )
            if valid_links:
                test_question.valid_links = valid_links
            test_question.save()
            questions[question_name] = test_question
        yield questions


@pytest.fixture
def question_text_with_links():
    test_question_text = [
        # test working link
        {
            'raw_text': '''
                 This patron saint of Lourdes'
                 <a href="http://www.j-archive.com/media/2004-11-17_DJ_21.jpg"
                 target="_blank">body</a>
                 has remained unchanged in its glass display case since her death in 1879
                 ''',
            'cleaned_text': 'This patron saint of Lourdes\' body has remained unchanged in its glass '
                            'display case since her death in 1879',
            'cleaned_links': ['http://www.j-archive.com/media/2004-11-17_DJ_21.jpg']
        },
        # test invalid link
        {
            'raw_text': '''
                     This patron saint of Lourdes'
                     <a href="https://www.j-archive.com/media/2004-11-17_DJ_21.jp"
                     target="_blank">body</a>
                     has remained unchanged in its glass display case since her death in 1879
                     ''',
            'cleaned_text': 'This patron saint of Lourdes\' body has remained unchanged in its glass '
                            'display case since her death in 1879',
            'cleaned_links': []
        },
        # test https link
        {
            'raw_text': '''
                         This patron saint of Lourdes'
                         <a href="https://www.j-archive.com/media/2004-11-17_DJ_21.jpg"
                         target="_blank">body</a>
                         has remained unchanged in its glass display case since her death in 1879
                         ''',
            'cleaned_text': 'This patron saint of Lourdes\' body has remained unchanged in its glass '
                            'display case since her death in 1879',
            'cleaned_links': ['https://www.j-archive.com/media/2004-11-17_DJ_21.jpg']
        },
        # test 404 link
        {
            'raw_text': '''
                <a href="http://www.j-archive.com/media/2010-06-15_DJ_20.jpg" \
                target="_blank">What</a> the ant had in song
                 ''',
            'cleaned_text': 'What the ant had in song',
            'cleaned_links': []
        },
        # invalid text
        {
            'raw_text': 'wrongtext  <a href="thisisntavalidlink"</a>  morewrongtext',
            'cleaned_text': 'wrongtext morewrongtext',
            'cleaned_links': []
        },
        # valid text with no links
        {
            'raw_text': 'This is the first king of Poland',
            'cleaned_text': 'This is the first king of Poland',
            'cleaned_links': []
        },
        # multiple links
        {
            'raw_text': '''
                <a href="http://www.j-archive.com/media/2007-12-13_DJ_28.jpg" \
                target="_blank">Jon of the Clue Crew holds a purple gem in a pair of tweezers.</a> \
                It has more iron oxide than any other variety of quartz, which is believed to \
                account for its rich \
                <a href="http://www.j-archive.com/media/2007-12-13_DJ_28a.jpg" target="_blank">\
                color</a>
                 ''',
            'cleaned_text': 'Jon of the Clue Crew holds a purple gem in a pair of tweezers. '
                            'It has more iron oxide than any other variety of quartz, '
                            'which is believed to account for its rich color',
            'cleaned_links': [
                "http://www.j-archive.com/media/2007-12-13_DJ_28.jpg",
                "http://www.j-archive.com/media/2007-12-13_DJ_28a.jpg"
            ]
        },
    ]
    yield test_question_text
