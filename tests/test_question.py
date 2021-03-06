# native
import os
import json
from sys import path as syspath
syspath.append(
os.path.abspath(
os.path.join(
os.path.dirname(__file__), os.path.pardir)))
from threading import Timer
from re import findall
# project
from src.question import Question
# third-party
import pytest


test_timer = Timer(1, None)
test_question = Question(Question.get_random_question(), test_timer)


def mock_question(question_string: str, ret_json=None):
    """
    creates a test question based on a slack-formatted string
    :param question_string: slack-formatted question string, e.g.
    "[NOW HEAR THIS!] [$500] [2001-01-09] 'It's the native wind instrument heard here, mate'"
    :param ret_json: optional, outputs as json formatted string if set to true
    :return: Question
    """
    reg_question = findall(r'(\[(.*?)\]|\'(.*?)$)', question_string)
    category = reg_question[0][1]
    value = reg_question[1][1]
    date = reg_question[2][1]
    text = reg_question[3][2]

    if ret_json:
        return {"category": category, "air_date": date, "question": text, "value": value}
    else:
        new_question = Question(Question.get_random_question(), test_timer)
        new_question.category, new_question.value, new_question.date, new_question.text, new_question.daily_double = \
            category, value, date, text, Question.is_daily_double(new_question.value)
        new_question.slack_text = new_question.format_slack_text(new_question)
        return new_question


def test_get_value():
    """
    we want to make sure that it's a valid Jeopardy point value,
    so it has to be in an increment of $100
    """
    value_no_dollar_sign = test_question.get_value()[1:]
    assert int(value_no_dollar_sign) % 100 == 0


@pytest.mark.parametrize("test_text, expected_output", [
 # test working link
 ('''
 This patron saint of Lourdes'
 <a href="http://www.j-archive.com/media/2004-11-17_DJ_21.jpg"
 target="_blank">body</a>
 has remained unchanged in its glass display case since her death in 1879
 ''',
 ['This patron saint of Lourdes\' body has remained unchanged in its glass\
 display case since her death in 1879',
 'http://www.j-archive.com/media/2004-11-17_DJ_21.jpg']),

 # test 404 link
 ('''
 <a href="http://www.j-archive.com/media/2010-06-15_DJ_20.jpg" \
 target="_blank">What</a> the ant had in song
 ''',
 'What the ant had in song'),

 ('wrongtext  <a href="thisisntavalidlink"</a>  morewrongtext', 'wrongtext morewrongtext'),

 ('This is the first king of Poland', 'This is the first king of Poland'),

 # spacing looks ugly, but we need it so the test doesn't have extra spaces
 ('<a href="http://www.j-archive.com/media/2007-12-13_DJ_28.jpg" \
 target="_blank">Jon of the Clue Crew holds a purple gem in a pair of tweezers.</a> \
  It has more iron oxide than any other variety of quartz, which is believed to \
  account for its rich \
  <a href="http://www.j-archive.com/media/2007-12-13_DJ_28a.jpg" target="_blank">\
  color</a>', ['Jon of the Clue Crew holds a purple gem in a pair of tweezers.\
 It has more iron oxide than any other variety of quartz,\
 which is believed to account for its rich color',\
  "http://www.j-archive.com/media/2007-12-13_DJ_28.jpg",\
  "http://www.j-archive.com/media/2007-12-13_DJ_28a.jpg"])
])
def test_separate_html(test_text, expected_output):
    assert test_question.separate_html(test_text) == expected_output


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
    assert test_question.is_daily_double(test_value) == expected_value


def test_filter_questions():
    # set up
    test_json = open('./test_files/test_questions.json').read()
    test_question_list = json.loads(test_json)
    test_category = 'HISTORY'

    mock_question_1 = mock_question('[POP CULTURE] [$2000] [2004-02-02] '
                                    '\'He\'s the beloved comic strip character seen here with his friend Albert, '
                                    'back in 1948', ret_json=True)
    mock_question_2 = mock_question('[NOW HEAR THIS!] [$500] [2001-01-09] '
                                    '\'It\'s the native wind instrument heard here, mate', ret_json=True)

    mock_question_list = [mock_question_1, mock_question_2]

    # act
    history_filter = test_question.filter_questions(test_question_list, banned_categories='history')
    science_filter = test_question.filter_questions(test_question_list, banned_categories=[
        'science', 'biology', 'chemistry'
    ])
    heard_seen_here_filter = test_question.filter_questions(
        test_question_list,
        banned_phrases=['heard here', 'seen here']
    )
    # tests filtering both, as we do when we init a Question instance
    category_and_phrase_filter = test_question.filter_questions(
        test_question_list,
        banned_categories='missing this category',
        banned_phrases=['heard here', 'seen here'],
    )
    category_filter = test_question.filter_questions(test_question_list, category=test_category)
    mock_filter = test_question.filter_questions(mock_question_list, banned_phrases=['heard here', 'seen here'])

    # assert
    for c in history_filter: assert c['category'] != 'HISTORY'
    for c in science_filter: assert c['category'] != 'SCIENCE'
    for q in heard_seen_here_filter: assert 'heard here' not in q['question']\
        and 'seen here' not in q['question']
    for q in category_and_phrase_filter: \
        assert 'heard here' not in q['question'] \
        and 'seen here' not in q['question'] \
        and q['category'] != 'missing this category'
    assert len(category_filter) > 0
    for q in category_filter:
        assert q['category'].lower() == test_category.lower()
    assert len(mock_filter) == 0


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
    assert test_question.convert_value_to_int(test_value) == expected_value


def test_get_questions_by_category():
    categorized_questions = Question.get_questions_by_category('history', test_timer)
    category_list = [q.category for q in categorized_questions]
    # if all categories are not the same the length of category_list set will be more than one
    assert len(set(category_list)) == 1
