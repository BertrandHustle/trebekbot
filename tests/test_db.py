from sys import path as syspath
from sqlalchemy import create_engine
syspath.append('c:\\users\\hooks\\documents\\programming\\projects\\trebekbot\\src')
from re import findall
from os import path, remove
import pytest
import db
import testing.postgresql

# set up test db
postgresql = testing.postgresql.Postgresql()
engine = create_engine(postgresql.url())
dsn = postgresql.dsn()
conn_string = 'dbname=' + dsn['database'] + ' ' +'user=' + dsn['user'] + ' ' +\
'host=' + dsn['host'] + ' ' + 'port=' + str(dsn['port'])
test_db = db.db(conn_string)
test_cursor = test_db.connection.cursor()

# fixture for cleaning out test users from database (but leaving table present)
@pytest.fixture
def scrub_test_users():
    yield scrub_test_users
    test_cursor.execute(
    '''
    DELETE FROM USERS
    '''
    )

# set up fixture to populate test db with a range of scorers
@pytest.fixture
def populate_db():
    test_users = ['Bob', 'Jim', 'Carol', 'Eve', 'Morp']
    test_score = 101
    # ensure that we have a varied list of scorers
    for user in test_users:
        test_db.add_user_to_db(test_db.connection, user)
        test_db.update_score(test_db.connection, user, test_score)
        test_score += 100
    # check to make sure negative numbers work too
    test_cursor.execute(
    '''
    UPDATE USERS SET SCORE = %s WHERE NAME = %s
    ''',
    (-156, 'Eve')
    )

# same as above, but all scores are zero
@pytest.fixture
def populate_db_all_scores_zero():
    test_users = ['Bob', 'Jim', 'Carol', 'Eve', 'Morp']
    for user in test_users:
        test_db.add_user_to_db(test_db.connection, user)


def test_add_user_to_db():
    # do this twice to ensure that we're adhering to the UNIQUE constraint
    test_db.add_user_to_db(test_db.connection, 'Bob')
    test_db.add_user_to_db(test_db.connection, 'Bob')
    test_query = test_cursor.execute(
    '''
    SELECT * FROM USERS WHERE NAME = %s
    ''',
    ('Bob',)
    )
    query_results = test_cursor.fetchall()
    check_results = findall(r'Bob', str(query_results))
    # asserts both that Bob was added and that he was only added once
    assert len(check_results) == 1
    assert type(query_results[0][0]) == int


@pytest.mark.parametrize("user, value_change, expected_result", [
 ('LaVar', '0', 0),
 ('LaVar', '-200', -200),
 ('LaVar', '-200', -400),
 ('LaVar', '500', 100),
 ('Stemp', 'Invalid Value', 0),
 ('boop', '-9000', -9000),
 ('boop', '-500', -9500),
 # the min score is -10000 to prevent players from going too far into the hole
 ('boop', '-1000', -10000),
 # this makes sense, if we get a non-int it should do nothing
 ('LaVar', 'ants', 100)
])
def test_update_score(user, value_change, expected_result):
    test_db.add_user_to_db(test_db.connection, user)
    test_db.update_score(test_db.connection, user, value_change)
    assert test_db.get_score(test_db.connection, user) == expected_result


# we can't do this above because it scrubs the db after EVERY parametrized test
# scrub_test_users()

test_cursor.execute('DELETE FROM USERS')


# TODO: test force flag
def test_return_top_ten(populate_db, scrub_test_users):
    # using just names so we don't run into ID conflicts
    expected_names = [
    'Morp',
    'Carol',
    'Jim',
    'Bob',
    'LaVar',
    'Stemp',
    'Eve',
    'boop'
    ]
    test_top_ten = test_db.return_top_ten(test_db.connection)
    top_ten_names = [x[1] for x in test_top_ten]
    assert len(test_top_ten) == 4
    assert top_ten_names == expected_names


def test_increment_win(populate_db, scrub_test_users):
    test_db.increment_win(test_db.connection, 'Carol')
    test_cursor.execute(
    '''
    SELECT WINS FROM USERS WHERE NAME = %s
    ''', ('Carol',)
    )
    assert test_cursor.fetchall()[0][0] == 1


def test_get_user_wins(populate_db, scrub_test_users):
    test_connection = test_db.connection
    test_db.increment_win(test_connection, 'Carol')
    test_db.increment_win(test_connection, 'Carol')
    test_db.increment_win(test_connection, 'Carol')
    test_query = test_db.get_user_wins(test_connection, 'Carol')
    assert test_query == 3


def test_get_champion(populate_db, scrub_test_users):
    expected_champion_name = 'Morp'
    expected_champion_score = 501
    assert test_db.get_champion(test_db.connection) == \
    (expected_champion_name, expected_champion_score)
    # create a tie
    test_cursor.execute(
    '''
    UPDATE USERS SET SCORE = %s WHERE NAME = %s
    ''',
    (10000, 'Bob')
    )
    test_cursor.execute(
    '''
    UPDATE USERS SET SCORE = %s WHERE NAME = %s
    ''',
    (10000, 'Jim')
    )
    expected_champion_names = ['Bob', 'Jim']
    expected_champion_scores = [10000, 10000]
    assert test_db.get_champion(test_db.connection) == \
    [(expected_champion_names[0], expected_champion_scores[0]),
     (expected_champion_names[1], expected_champion_scores[1])]


'''
not a real unit test, but used to test the edge case where there is no champ
for db.get_champion()
'''
def test_no_champion(scrub_test_users):
    assert test_db.get_champion(test_db.connection) == None


# TODO: test if user doesn't exist
def test_get_score(scrub_test_users):
    test_db.add_user_to_db(test_db.connection, 'Lucy')
    assert test_db.get_score(test_db.connection, 'Lucy') == 0
    test_cursor.execute(
    '''
    UPDATE USERS SET SCORE = %s WHERE NAME = %s
    ''',
    (100, 'Lucy')
    )
    assert test_db.get_score(test_db.connection, 'Lucy') == 100


def test_wipe_scores(populate_db):
    test_db.wipe_scores(test_db.connection)
    # get scores
    test_cursor.execute(
    '''
    SELECT * FROM USERS ORDER BY SCORE DESC
    ''',
    )
    test_scores = [x[2] for x in test_cursor.fetchall()]
    # this works because every score should be 0
    assert not any(test_scores)
