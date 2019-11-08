import os
from sys import path as syspath
syspath.append(
os.path.abspath(
os.path.join(
os.path.dirname(__file__), os.path.pardir)))
import pytest
import src.judge as judge

test_judge = judge.Judge()

def test_strip_answer(test_value, expected_value):
    assert test_judge.strip_answer(test_value) == expected_value

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
  given_answer = test_judge.strip_answer(given_answer)
  expected_answer = test_judge.strip_answer(expected_answer)
  # convert to set so we don't need to worry about ordering
  test_list = set(test_judge.pair_off_answers(given_answer, expected_answer))
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
    assert test_judge.fuzz_word(given_word, expected_word) == expected_value

# TODO: test this for crashing
'''
category": "MYTHOLOGICAL CROSSWORD CLUES \"M\"", "air_date": "1998-10-13",
"question": "'\"Touch\"y golden guy<br />             (5)'",
"value": "$200", "answer": "King Midas", "round": "Double Jeopardy!",
"show_number": "3242"}
'''

# time before async: 27.27 seconds
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
 # make sure we aren't too lenient for longer words
 ('featherweight', 'welterweight', False),
 # slashes
 ('istanbul', 'istanbul/constantinople', True),
 ('hag', 'hag tag', False),
 # before and after questions
 ('soup nazi dictator', 'Talk Soup Nazi', False)
])
def test_fuzz_answer(given_answer, expected_answer, expected_value):
    assert test_judge.fuzz_answer(given_answer, expected_answer) == expected_value

@pytest.mark.parametrize("given_answer, correct_answer, expected_reply", [
 ('princess di', 'Princess Diana', 'Please be more specific.'),
 ('general mills and general electric', 'General Motors & General Electric', \
 'Please be more specific.'),
 ('the almighty king of siam', 'the king of siam', 'Please be less specific.'),
 ('corporal klinger', 'max klinger', 'Please be more specific.')
])
def test_check_closeness(given_answer, correct_answer, expected_reply):
    assert test_judge.check_closeness(given_answer, correct_answer) == \
    expected_reply