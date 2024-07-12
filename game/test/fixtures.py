import json
from datetime import datetime
from pathlib import Path

import pytest

from game.models.Player import Player
from game.models.Question import Question
from paths import ROOT_DIR


@pytest.fixture
def test_player():
    yield Player.objects.create(username='Test Player')


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
