import pytest
import host
import question
import db
import slackclient
from re import findall
from os import remove
from main import slack_token

# set up test objects
sc = slackclient.SlackClient(slack_token)
test_question = question.Question()
test_host = host.Host(sc)
test_db = db.db('test.db')

# fixture for tearing down test database
@pytest.fixture
def db_after():
    print('test.db users dropped')
    yield db_after
    test_db.drop_table_users(test_db.connection)

# TODO: make this work so it deleted test db after test
# deletes test.db file
@pytest.fixture
def kill_test_db():
    print('test.db deleted')
    remove(test_db.db_file)

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
 (-1, False),
 (0, False),
 ('0', False)
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
 (600, 'Borth', False),
 (None, 'Borth', False),
 ('mary queen of scotts','Mary, Queen of Scots', True),
 ('','Mary, Queen of Scots', False),
 ('MAAAARYYYY QUEEN OF SCOOOOOOTTSSS','Mary, Queen of Scots', False),
 ('borp', 'Henry James', False)
])
def test_fuzz_answer(given_answer, expected_answer, expected_value):
    assert test_host.fuzz_answer(given_answer, expected_answer) == expected_value

# TODO: rewrite database tests using Mock
# TODO: add bad values in here e.g. ' ', 0
def test_add_user_to_db():
    # do this twice to ensure that we're adhering to the UNIQUE constraint
    test_db.add_user_to_db(test_db.connection, 'Bob')
    test_db.add_user_to_db(test_db.connection, 'Bob')
    test_query = test_db.connection.execute(
    '''
    SELECT * FROM USERS WHERE NAME = ?
    ''',
    ('Bob',)
    )
    query_results = test_query.fetchall()
    print(query_results)
    check_results = findall(r'Bob', str(query_results))
    # asserts both that Bob was added and that he was only added once
    assert len(check_results) == 1

def test_update_score():
    test_db.update_score(test_db.connection, user)
    assert test_db.return_score(test_db.connection=, user) == 200

def test_myscore(db_after):
    test_db.add_user_to_db(test_db.connection, 'Lucy')
    assert test_db.return_score(test_db.connection, 'Lucy') == 0
    test_db.connection.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
    ''',
    (100, 'Lucy')
    )
    assert test_db.return_score(test_db.connection, 'Lucy') == 100
