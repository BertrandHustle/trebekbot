import json

import pytest

from game.models import Question

@pytest.fixture()
def test_questions():
    questions = []
    with open('./test_files/test_questions.json') as test_question_json:
        for question_json in json.load(test_question_json):
