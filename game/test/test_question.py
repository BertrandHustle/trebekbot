import pytest

from django.test import RequestFactory

from .fixtures import question_text_with_links, test_questions
from game.models import Question


@pytest.fixture(scope='session', autouse=True)
def setup_question_get():
    req_factory = RequestFactory()
    yield req_factory.get('/game/question')


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


# def test_question_filtering():
#     # set up
#     test_json = open('test_files/test_questions.json').read()
#     test_question_list = json.loads(test_json)
#     test_category = 'HISTORY'
#
#     mock_question_1 = mock_question('[POP CULTURE] [$2000] [2004-02-02] '
#                                     '\'He\'s the beloved comic strip character seen here with his friend Albert, '
#                                     'back in 1948', ret_json=True)
#     mock_question_2 = mock_question('[NOW HEAR THIS!] [$500] [2001-01-09] '
#                                     '\'It\'s the native wind instrument heard here, mate', ret_json=True)
#
#     mock_question_list = [mock_question_1, mock_question_2]
#
#     # act
#     history_filter = test_question.filter_questions(test_question_list, banned_categories='history')
#     science_filter = test_question.filter_questions(test_question_list, banned_categories=[
#         'science', 'biology', 'chemistry'
#     ])
#     heard_seen_here_filter = test_question.filter_questions(
#         test_question_list,
#         banned_phrases=['heard here', 'seen here']
#     )
#     # tests filtering both, as we do when we init a Question instance
#     category_and_phrase_filter = test_question.filter_questions(
#         test_question_list,
#         banned_categories='missing this category',
#         banned_phrases=['heard here', 'seen here'],
#     )
#     category_filter = test_question.filter_questions(test_question_list, category=test_category)
#     mock_filter = test_question.filter_questions(mock_question_list, banned_phrases=['heard here', 'seen here'])
#
#     # assert
#     for c in history_filter: assert c['category'] != 'HISTORY'
#     for c in science_filter: assert c['category'] != 'SCIENCE'
#     for q in heard_seen_here_filter: assert 'heard here' not in q['question']\
#         and 'seen here' not in q['question']
#     for q in category_and_phrase_filter: \
#         assert 'heard here' not in q['question'] \
#         and 'seen here' not in q['question'] \
#         and q['category'] != 'missing this category'
#     assert len(category_filter) > 0
#     for q in category_filter:
#         assert q['category'].lower() == test_category.lower()
#     assert len(mock_filter) == 0


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

