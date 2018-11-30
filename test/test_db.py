from re import findall
from atexit import register
from os import path, remove
import pytest
import src.db as db

# TODO: use Mock for db

# set up test objects
test_db = db.db('test.db')

# kill db on exit
def kill_test_db():
    test_db.connection.close()
    return remove(test_db.filepath)

# fixture for tearing down test database completely
@pytest.fixture
def db_after():
    yield db_after
    test_db.drop_table_users(test_db.connection)

# fixture for cleaning out test users from database (but leaving table present)
# TODO: make this run after failed tests
@pytest.fixture
def scrub_test_users():
    yield scrub_test_users
    test_db.connection.execute(
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
    test_db.connection.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
    ''',
    (-156, 'Eve')
    )
    test_db.connection.execute(
    '''
    UPDATE USERS SET CHAMPION_SCORE = ? WHERE NAME = ?
    ''',
    (5000, 'Morp')
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
    test_query = test_db.connection.execute(
    '''
    SELECT * FROM USERS WHERE NAME = ?
    ''',
    ('Bob',)
    )
    query_results = test_query.fetchall()
    check_results = findall(r'Bob', str(query_results))
    # asserts both that Bob was added and that he was only added once
    assert len(check_results) == 1

@pytest.mark.parametrize("user, value_change, expected_result", [
 ('LaVar', '0', 0),
 ('LaVar', '-200', -200),
 ('LaVar', '-200', -400),
 ('LaVar', '500', 100),
 ('Stemp', 'Invalid Value', 0),
 ('boop', '-9000', -9000),
 ('boop', '-500', -9500),
 # this makes sense, if we get a non-int it should do nothing
 ('LaVar', 'ants', 100)
])
def test_update_score(user, value_change, expected_result):
    test_db.add_user_to_db(test_db.connection, user)
    test_db.update_score(test_db.connection, user, value_change)
    assert test_db.get_score(test_db.connection, user) == expected_result

# we can't do this above because it scrubs the db after EVERY parametrized test
scrub_test_users()

# TODO: test force flag
def test_return_top_ten(populate_db, scrub_test_users):
    expected_list = [
    (8, 'Morp', 501, 5000, 0, 0),
    (6, 'Carol', 301, 0, 0, 0),
    (5, 'Jim', 201, 0, 0, 0),
    (1, 'Bob', 101, 0, 0, 0),
    (2, 'LaVar', 100, 0, 0, 0),
    (3, 'Stemp', 0, 0, 0, 0),
    (7, 'Eve', -156, 0, 0, 0),
    (4, 'boop', -9500, 0, 0, 0)
    ]
    assert test_db.return_top_ten(test_db.connection) == expected_list

def test_increment_win(populate_db, scrub_test_users):
    test_connection = test_db.connection
    test_db.increment_win(test_connection, 'Carol')
    test_query = test_connection.cursor().execute(
    '''
    SELECT WINS FROM USERS WHERE NAME = ?
    ''', ('Carol',)
    )
    assert test_query.fetchall()[0][0] == 1

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
    test_db.connection.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
    ''',
    (10000, 'Bob')
    )
    test_db.connection.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
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
def test_no_champion(populate_db_all_scores_zero, scrub_test_users):
    assert test_db.get_champion(test_db.connection) == None

def test_get_last_nights_champion(populate_db, scrub_test_users):
    expected_champion_name = 'Morp'
    expected_champion_score = 5000
    assert test_db.get_last_nights_champion(test_db.connection) == \
    (expected_champion_name, expected_champion_score)

def test_set_champion(populate_db, scrub_test_users):
    test_db.set_champion(test_db.connection, 'Morp', 501)
    test_result = test_db.connection.execute(
    '''
    SELECT * FROM USERS WHERE CHAMPION = 1 AND CHAMPION_SCORE = 501
    '''
    ).fetchone()
    assert (test_result[1], test_result[3]) == ('Morp', 501)

# TODO: test if user doesn't exist
def test_get_score(scrub_test_users):
    test_db.add_user_to_db(test_db.connection, 'Lucy')
    assert test_db.get_score(test_db.connection, 'Lucy') == 0
    test_db.connection.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
    ''',
    (100, 'Lucy')
    )
    assert test_db.get_score(test_db.connection, 'Lucy') == 100

def test_wipe_scores(populate_db, db_after):
    test_db.wipe_scores(test_db.connection)
    # get scores
    test_scores = test_db.connection.execute(
    '''
    SELECT * FROM USERS ORDER BY SCORE DESC
    ''',
    ).fetchall()
    test_scores = [x[2] for x in test_scores]
    # this works because every score should be 0
    assert not any(test_scores)

register(kill_test_db)