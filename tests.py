import pytest
import host
import question
import db
import slackclient
from main import slack_token

# set up test objects
sc = slackclient.SlackClient(slack_token)
test_question = question.Question()
test_host = host.Host(sc)
test_db = db.db('test.db')

# tests question constructor
def test_question_constructor():
    assert type(test_question.answer) == str
    assert type(test_question.category) == str
    assert type(test_question.daily_double) == bool
    assert type(test_question.text) == str
    assert type(test_question.value) == int

def test_get_value():
    '''
    we want to make sure that it's a valid Jeopardy point value,
    so it has to be in an increment of $100
    '''
    value_no_dollar_sign = test_question.get_value()[2:]
    assert int(value_no_dollar_sign) % 100 == 0

@pytest.mark.parametrize("test_value, expected_value", [
 ('$100', False),
 ('$5578', True),
 (200, False),
 (10239, True),
 (1, False),
 (-1, 'Invalid Value'),
 (0, 'Invalid Value'),
 ('0', 'Invalid Value')
])
def test_is_daily_double(test_value, expected_value):
    assert test_question.is_daily_double(test_value) == expected_value

@pytest.mark.parametrize("test_value, expected_value", [
 ('$2,500', 2500),
 ('asjdjasdj', 'Invalid Value'),
 (0, 'Invalid Value'),
 (-1, 'Invalid Value'),
 (-888, 'Invalid Value'),
 ('-$4,001', 'Invalid Value'),
 (None, 'Invalid Value')
])
def test_convert_value_to_int(test_value, expected_value):
    assert test_question.convert_value_to_int(test_value) == expected_value

@pytest.mark.parametrize("given_answer, expected_answer, expected_value", [
 ('Bath', 'Borth', False),
 ('Bath', 'beth', False),
 (600, 'Borth', 'Invalid Value'),
 (None, 'Borth', 'Invalid Value'),
 ('mary queen of scotts','Mary, Queen of Scots', True),
 ('','Mary, Queen of Scots', 'Invalid Value'),
 ('MAAAARYYYY QUEEN OF SCOOOOOOTTSSS','Mary, Queen of Scots', False)
])
def test_fuzz_answer(given_answer, expected_answer, expected_value):
    assert test_host.fuzz_answer(given_answer, expected_answer) == expected_value

# TODO: rewrite database tests using Mock
'''
@pytest.mark.parametrize("test_user", "expected_output", [
 ('Bob', 'Bob'),
 (77, False),
])
'''
def test_add_user_to_db():
    test_db.add_user_to_db(test_db.connection, 'Bob')
    test_query = test_db.connection.execute(
    '''
    SELECT * FROM USERS WHERE NAME = ?
    ''',
    ('Bob',)
    )
    assert 'Bob' in test_query.fetchall()[1]
