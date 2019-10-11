import os
from sqlalchemy import create_engine
from sys import path as syspath
syspath.append(
os.path.abspath(
os.path.join(
os.path.dirname(__file__), os.path.pardir)))
import src.host as host
import src.db as db
import pytest
import slackclient
import testing.postgresql

# set up test objects
sc = slackclient.SlackClient(os.environ['TREBEKBOT_API_TOKEN'])

# set up test db
postgresql = testing.postgresql.Postgresql()
engine = create_engine(postgresql.url())
dsn = postgresql.dsn()
conn_string = 'dbname=' + dsn['database'] + ' ' +'user=' + dsn['user'] + ' ' +\
'host=' + dsn['host'] + ' ' + 'port=' + str(dsn['port'])
test_db = db.db(conn_string)


# TODO: find a way to make this not duplicate code from test_db
def populate_db(database):
    test_users = ['Bob', 'Jim', 'Carol', 'Eve', 'Morp']
    test_score = 101
    # ensure that we have a varied list of scorers
    for user in test_users:
        database.add_user_to_db(database.connection, user)
        database.update_score(database.connection, user, test_score)
        test_score += 100
    # guarantee user with 0 score
    database.add_user_to_db(database.connection, 'Scott')
    test_cursor = database.connection.cursor()
    # check to make sure negative numbers work too
    test_cursor.execute(
    '''
    UPDATE USERS SET SCORE = %s WHERE NAME = %s
    ''',
    (-156, 'Eve')
    )

populate_db(test_db)
test_host = host.Host(sc, test_db)


def test_get_bot_id():
    expected_id = "U5YKR45PB"
    assert test_host.get_bot_id('trebekbot') == expected_id


@pytest.mark.parametrize("wager, user_score, expected_value", [
 ('aw, he restarted', 1500, None),
 (500, 500, 500),
 ('bees', 1500, None),
 # this will prompt trebekbot to re-ask for a wager
 (0, 0, None),
 (-500, 2500, None),
 # test jeopardy minimum of 1000 rule
 (1000, 100, 1000),
 (10000, 100, 1000)
])
def test_calc_wager(wager, user_score, expected_value):
    assert test_host.calc_wager(wager, user_score) == expected_value

@pytest.mark.parametrize("test_value, expected_value", [
 # we add an extra space because this is how we get the answers from slack
 (' Hall & Oates', ['hall', 'oates']),
 (' Hall and Oates', ['hall', 'oates']),
 (' Androgynous', ['androgynous']),
 (' Hall & Oates\' Oats and Halls', ['hall', 'oates', 'oats', 'halls']),
 ('the absolute density of a dying star', \
 ['absolute', 'density', 'dying', 'star']),
 (' "The Little Rascals"', ['little', 'rascals']),
 ('(the) Dow (Jones)', ['dow']),
 ('S-P-E-L-L-I-N-G', ['spelling']),
 # test extra whitespace
 (' S-P-E-L-L-I-N-G', ['spelling'])
])
def test_get_latest_changelog():
    changelog = '../support_files/test_README.md'
    expected_changelog = ['version 0.5.3 changelog (4-5-18):',
    '',
    'Bugs:',
    '  - fixed crash from querying slack api for channel',
    "  - fixed issue with 'spelling bee' questions",
    '  - parentheses in answers now treated as optional to the answer',
    '',
    'Features:',
    '  - trebekbot now announces latest changes on startup',
    '']
    test_changelog = test_host.get_latest_changelog(changelog).split('\n')[:-1]
    assert test_changelog == expected_changelog
