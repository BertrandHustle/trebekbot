import json

import pytest

from game.serializers import QuestionSerializer


@pytest.fixture()
def test_questions():
    with open('game/test/test_files/test_questions.json') as test_question_json_file:
        questions = {}
        question_json = json.load(test_question_json_file)
        for question_name, question in question_json.items():
            serializer = QuestionSerializer(data=question)
            serializer.is_valid()
            question = serializer.create(serializer.data)
            questions[question_name] = question
        yield questions
