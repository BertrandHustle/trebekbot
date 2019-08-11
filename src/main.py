author = 'bertrand_hustle'
bot_name = 'trebekbot'

# Main file for trebekbot
import sys
import os
import src.question as question
import src.db as db
import src.host as host
import urllib.parse as urlparse
from threading import Timer
from slackclient import SlackClient
from flask import Flask, jsonify, request

app = Flask(__name__)

# setup database (or connect to existing one)
# thanks to joamag on stackoverflow
result = urlparse.urlparse(os.environ['DATABASE_URL'])
dbuser = result.username
password = result.password
dbname = result.path[1:]
dbhost = result.hostname
user_db = db.db(
    'dbname=' + dbname + ' ' +
    'user=' + dbuser + ' ' +
    'password=' + password + ' ' +
    'host=' + dbhost + ' ' +
    'sslmode=require'
)
# retrieve id/token/etc. from env variables
slack_token = os.environ['TREBEKBOT_API_TOKEN']
slack_client = SlackClient(slack_token)
# NOTE: do not use # in the name, slack's api returns the channel name only
channel = 'trivia'
# export channel to env so host can grab it
os.environ['SLACK_CHANNEL'] = channel
# time limit for questions
time_limit = 60
# vars for daily doubles
wager = 0
# if question is daily double only this user can answer
daily_double_asker = None
# check if we have a live question
question_is_live = False

# resets timer/wager and removes active question and answer
def reset_timer():
    global live_question
    global question_is_live
    host.say(channel, "Sorry, we're out of time. The correct answer is: " + live_question.answer)
    question_is_live = False
    wager = 0
    # generate new question
    live_question = question.Question(Timer(time_limit, reset_timer))

# load this in the background to speed up response time
live_question = question.Question(Timer(time_limit, reset_timer))

# say hi!
@app.route('/hello', methods=['POST'])
def hello():
    # TODO: make decorator to get username/id
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    payload = {
    'text' : 'Hello ' + host.create_user_address(user_name, user_id),
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

host = host.Host(slack_client, user_db)

# display help text
@app.route('/howtoplay', methods=['POST'])
def howtoplay():
    payload = {
    'text' : host.help_text,
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# display latest changelog
@app.route('/changelog', methods=['POST'])
def changelog():
    payload = {
    'text' : host.get_latest_changelog('README.md'),
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# display uptime for trebekbot
@app.route('/uptime', methods=['POST'])
def uptime():
    ayload = {
    'text' : 'uptime: ' + host.uptime,
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# TODO: clean up global refs
# trebekbot asks a question
@app.route('/ask', methods=['POST'])
def ask():
    global live_question
    global daily_double_asker
    global question_is_live
    payload = {'text': None, 'response_type': 'in_channel'}
    # check if question has active timer
    if not question_is_live:
        if live_question.is_daily_double:
            user_name = request.form['user_name']
            user_id = request.form['user_id']
            payload['text'] = live_question.slack_text
            payload['text'] += '\n' + host.create_daily_double_address(
                user_name, user_id
            )
            # if question is daily double we need to track who received it
            daily_double_asker = request.form['user_name']
        else:
            payload['text'] = live_question.slack_text
        # TODO: add time to timer if daily double
        # start question timer
        live_question.timer.start()
        question_is_live = True
    else:
        payload['text'] = 'question is already in play!'
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# forces skip on current question and generates new question
@app.route('/skip', methods=['POST'])
def skip():
    global live_question
    global daily_double_asker
    # cancel current timer and instantiate new question
    live_question.timer.cancel()
    live_question = question.Question(Timer(time_limit, reset_timer))
    payload = {'text': None, 'response_type': 'in_channel'}
    if live_question.is_daily_double:
        user_name = request.form['user_name']
        user_id = request.form['user_id']
        payload['text'] = live_question.slack_text
        payload['text'] += '\n' + host.create_daily_double_address(
            user_name, user_id
        )
        # if question is daily double we need to track who received it
        daily_double_asker = request.form['user_name']
    else:
        payload['text'] = live_question.slack_text
    # TODO: add time to timer if daily double
    # start question timer
    live_question.timer.start()
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# get wager for daily double
@app.route('/wager', methods=['POST'])
def wager():
    global wager
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    wager = request.form['text']
    payload = {
    'text' : host.get_wager(wager, user_name, user_id),
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# pass daily double if user doesn't know answer
@app.route('/nope', methods=['POST'])
def nope():
    global wager
    payload = {
    'text' : 'Coward. The correct answer is ' + live_question.answer,
    'response_type' : 'in_channel'
    }
    if wager:
        payload['text'] = 'You can\'t pass if you\'ve already wagered!'
    payload = jsonify(payload)
    payload.status_code = 200
    live_question.timer.cancel()
    live_question = question.Question(Timer(time_limit, reset_timer))
    question_is_live = False
    return payload

# answer the current question
@app.route('/whatis', methods=['POST'])
def whatis():
    global live_question
    global daily_double_asker
    global wager
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    answer = request.form['text']
    payload = {'text' : None, 'response_type' : 'in_channel'}
    # if someone else tries to answer daily double
    if live_question.is_daily_double and user_name != daily_double_asker:
        payload['text'] = 'Not your daily double!'
        payload = jsonify(payload)
        payload.status_code = 200
        return payload
    # if someone tries to answer daily double without wagering
    elif live_question.is_daily_double and not wager:
        payload['text'] = 'Please wager something first (not zero!).'
        payload = jsonify(payload)
        payload.status_code = 200
        return payload
    else:
        answer_check = host.check_answer(
            live_question,
            answer,
            user_name,
            user_id,
            wager=wager
        )
        payload['text'] = answer_check
        # if answer is correct we need to reset timer/wager and
        # wipe out live question
        if ':white_check_mark:' in answer_check:
            live_question.timer.cancel()
            wager = 0
            live_question = question.Question(Timer(time_limit, reset_timer))
            question_is_live = False
        payload = jsonify(payload)
        payload.status_code = 200
        return payload


# get user's score
@app.route('/myscore', methods=['POST'])
def myscore():
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    payload = {
    'text': host.my_score(user_name, user_id),
    'response_type': 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# get user's tally of all-time wins
@app.route('/mywins', methods=['POST'])
def mywins():
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    payload = {
    'text': host.mywins(user_name, user_id),
    'response_type': 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# get list of all users' scores
@app.route('/topten', methods=['POST'])
def topten():
    payload = {
    'text': host.top_ten(),
    'response_type': 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# DEBUG Routes

# used to force a daily double for testing
@app.route('/dd', methods=['POST'])
def dd():
    global live_question
    global daily_double_asker
    payload = {'text': None, 'response_type': 'in_channel'}
    if request.form['user_name'] == 'bertrand_hustle':
        live_question = question.Question(Timer(time_limit, reset_timer), daily_double_debug=True)
        user_name = request.form['user_name']
        user_id = request.form['user_id']
        payload['text'] = live_question.slack_text
        payload['text'] += '\n' + host.create_daily_double_address(
            user_name, user_id
        )
        daily_double_asker = user_name
        # TODO: add time to timer if daily double
        live_question.start_timer()
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# force crash/restart trebekbot
@app.route('/crash', methods=['POST'])
def crash():
    raise Exception

# shows debug info
@app.route('/debug', methods=['POST'])
def debug():
    global live_question
    global question_is_live
    global wager
    debug_text = '''
    question = {}
    question is_alive = {}
    question live = {}
    wager = {}
    '''.format(
    live_question.slack_text,
    live_question.timer.is_alive,
    question_is_live,
    wager
    )
    payload = {
        'text': live_question.slack_text,
        'response_type': 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# NOTE: set WEB_CONCURRENCY=1 to stop duplication problem
if __name__=='__main__':
    # start main game
    app.run_server(debug=False, use_reloader=False)
    # app.run()
