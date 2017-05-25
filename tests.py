import pytest
import host
import question
import slackclient
from main import slack_token

sc = slackclient.SlackClient(slack_token)
test_question = question.Question()
test_host = host.Host(sc)

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

'''
@pytest.mark.parametrize("test_value, expected_value", [
 ('$2,500', 2500),
 ('asjdjasdj', 'Invalid Value'),
 (0, 'Invalid Value'),
 (-1, 'Invalid Value'),
 (-888, 'Invalid Value'),
 ('-$4,001', 'Invalid Value')
 (None, 'Invalid Value')
])
def test_convert_value_to_int(test_value, expected_value):
    assert question.convert_value_to_int(test_value) == expected_value

@pytest.mark.parametrize("given_answer, expected_answer, expected_value", [
 ('Bath', 'Borth', False),
 ('Bath', ';;!!!', False),
 ('Bath', 'beth', True),
 (600, 'Borth', False),
 (None, 'Borth', False),
 ('mary queen of scotts','Mary, Queen of Scots', True),
 ('','Mary, Queen of Scots', False),
 ('MAAAARYYYY QUEEN OF SCOOOOOOTTSSS','Mary, Queen of Scots', False)
])
def test_fuzz_answer(given_answer, expected_answer, expected_value):
    assert host.fuzz_answer(given_answer, expected_answer) == expected_value
'''
