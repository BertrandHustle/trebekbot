from sys import path as syspath
syspath.append('c:\\users\\hooks\\documents\\programming\\projects\\trebekbot\\src')
import question
import pytest

test_question = question.Question()

# tests question constructor
def test_question_constructor():
    assert type(test_question.answer) == str
    assert type(test_question.category) == str
    assert type(test_question.daily_double) == bool
    assert type(test_question.text) == str and test_question.text != ''
    assert type(test_question.value) == int
    assert type(test_question.date) == str
    assert type(test_question.slack_text) == str
    if test_question.valid_links:
        assert type(test_question.valid_links) == list
        for link in test_question.valid_links:
            assert link.startswith('http://')

def test_get_value():
    '''
    we want to make sure that it's a valid Jeopardy point value,
    so it has to be in an increment of $100
    '''
    value_no_dollar_sign = test_question.get_value()[2:]
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

'''
not a strict unit test, but used to test new daily_double param on Question
this is used for the host.debug_daily_double method
'''
def test_get_daily_double():
    test_question = question.Question(daily_double=True)
    assert test_question.daily_double == True

def test_filter_questions():
    # set up
    test_question_list = [
    {"category": "HISTORY",
    "air_date": "2004-12-31",
    "question": "'For the last 8 years of his life, Galileo was under house\
     arrest for espousing this man's theory, seen here'",
    "value": "$200",
    "answer": "Copernicus",
    "round": "Jeopardy!",
    "show_number": 4680},

    {"category": "SCIENCE",
    "air_date": "2004-12-31",
    "question": "'For the last 8 years of his life, Galileo was under house\
     arrest for espousing this man's theory, heard here'",
    "value": "$201",
    "answer": "Copernicus",
    "round": "Jeopardy!",
    "show_number": 4680},

    {"category": "BIOLOGY",
    "air_date": "2004-12-31",
    "question": "'For the last 8 years of his life, Galileo was under house\
     arrest for espousing this man's theory'",
    "value": "$0",
    "answer": "Copernicus",
    "round": "Jeopardy!",
    "show_number": 4680},

    {"category": "BIOLOGY",
    "air_date": "2004-12-31",
    "question": "'Heard here, for the last 8 years of his life, Galileo was \
    under house arrest for espousing this man's theory'",
    "value": "$0",
    "answer": "Copernicus",
    "round": "Jeopardy!",
    "show_number": 4680},

    {"category": "test",
    "air_date": "2000-00-00",
    "question": "He's the beloved comic strip character seen here text text",
    "value": "$2000",
    "answer": "bubbo",
    "round": "round",
    "show_number": 21389183}
    ]

    # act
    dd_filter = test_question.filter_questions(test_question_list, daily_double=1)
    history_filter = test_question.filter_questions(test_question_list, banned_categories='history')
    science_filter = test_question.filter_questions(test_question_list, banned_categories=['science', 'biology', 'chemistry'])
    heard_seen_here_filter = test_question.filter_questions(
    test_question_list,
    banned_categories=['test', 'test2'],
    banned_phrases=['heard here', 'seen here']
    )

    # assert
    for c in dd_filter: assert test_question.is_daily_double(c['value'])
    for c in history_filter: assert c['category'] != 'HISTORY'
    assert len(science_filter) == 2 and science_filter[0]['category'] not in ['science', 'biology', 'chemistry']
    assert len(heard_seen_here_filter) == 1
    for x in ['heard here', 'seen here']:
        assert x not in heard_seen_here_filter[0]['question']

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
