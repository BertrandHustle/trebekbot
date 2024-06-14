import json

import pytest

from game.models.Question import Question
from game.serializers import QuestionSerializer


@pytest.fixture()
def test_questions():
    with open('game/test/test_files/test_questions.json') as test_question_json_file:
        questions = {}
        question_json = json.load(test_question_json_file)
        for question_name, question in question_json.items():
            question['text'], question['valid_links'] = Question.separate_html(question['question'])
            serializer = QuestionSerializer(data=question)
            serializer.is_valid()
            question = serializer.create(serializer.data)
            questions[question_name] = question
        yield questions


@pytest.fixture()
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
