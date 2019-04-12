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
import json
import slackclient
import testing.postgresql

# set up test objects
sc = slackclient.SlackClient('slack_token')

# set up test db
postgresql = testing.postgresql.Postgresql()
engine = create_engine(postgresql.url())
test_db = db.db(**postgresql.dsn)

# TODO: find a way to make this not duplicate code from test_db
def populate_db(database):
    test_users = ['Bob', 'Jim', 'Carol', 'Eve', 'Morp']
    test_score = 101
    # ensure that we have a varied list of scorers
    for user in test_users:
        database.add_user_to_db(database.connection, user)
        database.update_score(database.connection, user, test_score)
        test_score += 100
    test_cursor = database.connection.cursor()
    # check to make sure negative numbers work too
    test_cursor.execute(
    '''
    UPDATE USERS SET SCORE = ? WHERE NAME = ?
    ''',
    (-156, 'Eve')
    )
    test_cursor.execute(
    '''
    UPDATE USERS SET CHAMPION_SCORE = ? WHERE NAME = ?
    ''',
    (5000, 'Morp')
    )

populate_db(test_db)
test_host = host.Host(sc)

def test_get_channel_id():
    fail_test_json = {"ok": False, "error": "invalid_auth"}
    test_json = json.load(open(path.join('support_files', 'json', 'test_get_channel_id.json')))
    expected_id = 'C600FK4T1'
    assert test_host.get_channel_id_from_json('trivia', test_json) == expected_id
    assert test_host.get_channel_id_from_json('trivia', fail_test_json) == None
    assert test_host.get_channel_id_from_json('trivia', None) == None

def test_get_bot_id():
    expected_id = "0"
    assert test_host.get_bot_id('trebekbot') == expected_id

@pytest.mark.parametrize("wager, user_score, expected_value", [
 ('aw, he restarted', 1500, None),
 (500, 500, 500),
 ('bees', 1500, None),
 # this will prompt trebekbot to re-ask for a wager
 (0, 0, None),
 (-500, 2500, 0),
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
def test_strip_answer(test_value, expected_value):
    assert test_host.strip_answer(test_value) == expected_value

@pytest.mark.parametrize("given_answer, expected_answer, expected_list", [
 ('Bath' , 'Borth', [('bath', 'borth')]),
 ('the dover cliffs', 'The White Cliffs of Dover', \
 [('dover', 'white'), ('dover', 'cliffs'), ('cliffs', 'white'), \
 ('dover', 'dover'), ('cliffs', 'cliffs')]),
 ('the dover cliffs', 'the cover dliffs', \
 [('dover', 'cover'), ('dover', 'dliffs'), ('cliffs', 'dliffs'), ('cliffs', 'cover')]),
 ('mary queen of scotts', 'Mary, Queen of Scots', \
 [('mary', 'mary'), ('mary', 'queen'), ('mary', 'scots'), \
 ('queen', 'queen'), ('queen', 'scots'), \
 ('scotts', 'mary'), ('scotts', 'queen'), ('scotts', 'scots')],
 )
])
def test_pair_off_answers(given_answer, expected_answer, expected_list):
  # it's assumed that we'll be doing this first in our regular answer checking
  given_answer = test_host.strip_answer(given_answer)
  expected_answer = test_host.strip_answer(expected_answer)
  # convert to set so we don't need to worry about ordering
  test_list = set(test_host.pair_off_answers(given_answer, expected_answer))
  expected_list = set(expected_list)
  assert test_list == expected_list

@pytest.mark.parametrize("given_word, expected_word, expected_value", [
  ('Test', 'Toast', False),
  ('Test', 'Tost', True),
  ('Test', 'te', False),
  ('bethlehem', 'bethelhem', 'close'),
  ('t', 'testaholic', False),
  ('Mr. Rodney', 'Mr. Rogers', False),
  ('Mr. Rodgers', 'Mr. Rogers', True),
  ('Mr. Roerss', 'Mr. Rogers', 'close')
])
def test_fuzz_word(given_word, expected_word, expected_value):
    assert test_host.fuzz_word(given_word, expected_word) == expected_value

# TODO: test this for crashing
'''
category": "MYTHOLOGICAL CROSSWORD CLUES \"M\"", "air_date": "1998-10-13",
"question": "'\"Touch\"y golden guy<br />             (5)'",
"value": "$200", "answer": "King Midas", "round": "Double Jeopardy!",
"show_number": "3242"}
'''

@pytest.mark.parametrize("given_answer, expected_answer, expected_value", [
 ('Bath', 'Borth', False),
 ('Bath', 'beth', True),
 (None, 'Borth', False),
 ('mary queen of scotts','Mary, Queen of Scots', True),
 ('','Mary, Queen of Scots', False),
 ('MAAAARYYYY QUEEN OF SCOOOOOOTTSSS','Mary, Queen of Scots', False),
 ('borp', 'Henry James', False),
 ('bagpipe', 'a bagpipe', True),
 ('amber alert', 'an Amber alert', True),
 ('infintesimal', 'infinitesimal', True),
 ('infiniitesimal', 'infinitesimal', True),
 ('the good Samaritan', 'The Good Samaritan', True),
 ('it’s a wonderful life', 'It\'s A Wonderful Life', True),
 ('Hall and Oates', 'Hall & Oates', True),
 ('b', 'the Boston Massacre', False),
 ('omlette', 'Denver omelette', 'close'),
 ('The Great Star of Bethlehem', 'The Star of Bethelhem', 'close'),
 ('lawn', 'The Great Lawn', 'close'),
 ('bechamel', 'béchamel', True),
 ('queen elizabeth ii', 'Elizabeth II', True),
 ('issac newton', 'Newton', 'close'),
 # test optional parentheses
 ('the dow jones', '(the) Dow (Jones)', True),
 ('dow', '(the) Dow (Jones)', True),
 ('Red and Green', 'Green and Red', True),
 ('Blue or green', 'Green', True),
 ('poker', 'a poker face', 'close'),
 ('the gay 90\'s', 'The Gay \'90s', True),
 ('REM', 'R.E.M.', True),
 ('hard days night', '"A Hard Day\'s Night"', True),
 ('HG Wells', '(H.G.) Wells', True),
 ('cat\'s in the cradle', 'Cats In The Cradle', True),
 ('Zermelo Frankel set theory', 'Zermelo-Frankel Set Theory', True),
 ('00', '00', True),
 ('91', '21', False),
 ('32', '32', True),
 ('the absolute density of a dying star', 'star', False),
 ('star', 'the absolute density of a dying star', False),
 ('world war 2', 'World War II', True),
 # special case for spelling bee questions, may need to filter those out
 ('Rorschach', 'R-O-R-S-C-H-A-C-H', True),
 ('R&D', 'R&D', True),
 ('L', 'Y', False),
 ('8', '4 pounds', False),
 # make sure we arent' too lenient for longer words
 ('featherweight', 'welterweight', False),
 # slashes
 ('istanbul', 'istanbul/constantinople', True)
])
def test_fuzz_answer(given_answer, expected_answer, expected_value):
    assert test_host.fuzz_answer(given_answer, expected_answer) == expected_value

@pytest.mark.parametrize("given_answer, correct_answer, expected_reply", [
 ('princess di', 'Princess Diana', 'Please be more specific.'),
 ('general mills and general electric', 'General Motors & General Electric', \
 'Please be more specific.'),
 ('the almighty king of siam', 'the king of siam', 'Please be less specific.'),
 ('corporal klinger', 'max klinger', 'Please be more specific.')
])
def test_check_closeness(given_answer, correct_answer, expected_reply):
    assert test_host.check_closeness(given_answer, correct_answer) == \
    expected_reply

@pytest.mark.parametrize("slack_output, user_score, expected_value", [
 ([{'source_team': 'T0LR9NXQQ', 'team': 'T0LR9NXQQ', 'text':
 '..wager 20000', 'type': 'message', 'ts': '1497097067.238474',
 'user': 'U1UU5ARJ6', 'channel': 'C5LMQHV5W'}], -5000, 1000),
 ([{'source_team': 'T0LR9NXQQ', 'team': 'T0LR9NXQQ', 'text':
 '..wager 10000', 'type': 'message', 'ts': '1497097067.238474',
 'user': 'U1UU5ARJ6', 'channel': 'C5LMQHV5W'}], 10000, 10000),
 ([{'source_team': 'T0LR9NXQQ', 'team': 'T0LR9NXQQ', 'text':
 '..wager 0', 'type': 'message', 'ts': '1497097067.238474',
 'user': 'U1UU5ARJ6', 'channel': 'C5LMQHV5W'}], 10000, None)
])
def test_get_wager(slack_output, user_score, expected_value):
    assert test_host.get_wager(slack_output, user_score) == expected_value

def test_get_latest_changelog():
    changelog = 'support_files/test_README.md'
    test_latest_changelog = ['version 0.5.3 changelog (4-5-18):',
    '',
    'Bugs:',
    '  - fixed crash from querying slack api for channel',
    "  - fixed issue with 'spelling bee' questions",
    '  - parentheses in answers now treated as optional to the answer',
    '',
    'Features:',
    '  - trebekbot now gives a top ten list of scorers before nightly restarts',
    '  - increased daily double timer to 90 seconds',
    '']
    print(test_host.get_latest_changelog(changelog).split('\n'))
    assert test_host.get_latest_changelog(changelog).split('\n')[:-1] \
    == test_latest_changelog
