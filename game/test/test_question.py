import pytest

from .fixtures import question_text_with_links, test_questions
from game.models import Question


def test_get_value(test_questions):
    """
    we want to make sure that it's a valid Jeopardy point value,
    so it has to be in an increment of $100
    """
    value_no_dollar_sign = test_questions['valid_question'].get_value()[1:]
    print(test_questions['valid_question'])
    assert int(value_no_dollar_sign) % 100 == 0

    value_no_dollar_sign = test_questions['invalid_value'].get_value()[1:]
    assert int(value_no_dollar_sign) % 100 != 0


def test_separate_html(question_text_with_links):
    for question in question_text_with_links:
        text, valid_links = Question.separate_html(question['raw_text'])
        assert text == question['cleaned_text']
        assert valid_links == question['cleaned_links']


@pytest.mark.parametrize("test_value, expected_value", [
 ('$100', False),
 ('$5578', True),
 (200, False),
 ('$201', True),
 (10239, True),
 (1, True),
 (-1, True),
 (0, True),
 ('0', True),
 ('$0', True)
])
def test_is_daily_double(test_value, expected_value):
    assert Question.is_daily_double(test_value) == expected_value


@pytest.mark.parametrize("test_value, expected_value", [
 ('$2,500', 2500),
 ('asjdjasdj', 0),
 (0, 0),
 (-1, 0),
 (-888, 0),
 ('-$4,001', 0),
 (None, 0)
])
def test_convert_value_to_int(test_value, expected_value):
    assert Question.convert_value_to_int(test_value) == expected_value
