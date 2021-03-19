author = 'bertrand_hustle'
bot_name = 'trebekbot'

# Main file for trebekbot
# built-ins
import os
import urllib.parse as urlparse
from threading import Timer, Thread
from json import dumps
# trebekbot classes
from src.db import db
from src.host import Host
from src.judge import Judge
from src.question import Question
# third-party libs
from flask import Flask, jsonify, request, Response
from requests import post
from slack import WebClient

app = Flask(__name__)

# setup database (or connect to existing one)
result = urlparse.urlparse(os.environ['DATABASE_URL'])
dbuser = result.username
password = result.password
dbname = result.path[1:]
dbhost = result.hostname
user_db = db(
    'dbname=' + dbname + ' ' +
    'user=' + dbuser + ' ' +
    'password=' + password + ' ' +
    'host=' + dbhost + ' ' +
    'sslmode=require'
)
# retrieve id/token/etc. from env variables
slack_token = os.environ['TREBEKBOT_API_TOKEN']
slack_client = WebClient(token=slack_token)
# NOTE: do not use # in the name, slack's api returns the channel name only
channel = 'trivia'
# export channel to env so host can grab it
os.environ['SLACK_CHANNEL'] = channel
# time limit for questions
time_limit = 60
# vars for daily doubles
current_wager = 0
# if question is daily double only this user can answer
daily_double_asker = None
# check if we have a live question
question_is_live = False
# generic wrong channel payload
wrong_channel_payload = {
    'text': 'Wrong channel!',
    'response_type': 'in_channel'
}
# hold all questions of the same category for /next route
categorized_questions = []


# TODO: add 500 error handler

# Utility Functions

# checks answer in background as thread
def answer_check_worker(answer, user_name, user_id):
    global live_question
    global daily_double_asker
    global current_wager
    global question_is_live
    global categorized_questions
    # necessary to keep flask from complaining about being out of scope for threading
    with app.app_context():
        if os.path.exists('answer_lock'):
            slack_client.chat_postMessage(
                channel=channel,
                text='Another user has already buzzed in!',
                as_user=True
            )
        else:
            # lock file to prevent multiple people answering at once
            with open('answer_lock', 'w') as lock:
                lock.write('locked')
            answer_check = host.check_answer(live_question, answer, user_name, user_id, wager=current_wager)
            # prep for /next route if someone wants the same category for next question
            categorized_questions = Question.get_questions_by_category(
                live_question.category, Timer(time_limit, reset_timer)
            )
            # answer is correct: reset timer/wager and wipe out live question
            if ':white_check_mark:' in answer_check:
                live_question.timer.cancel()
                current_wager = 0
                live_question = Question(Question.get_random_question(), Timer(time_limit, reset_timer))
                question_is_live = False
            host.say(channel, answer_check)
            os.remove('answer_lock')


# resets timer/wager and removes active question and answer
def reset_timer():
    global live_question
    global question_is_live
    global categorized_questions
    global current_wager
    host.say(channel, "Sorry, we're out of time. The correct answer is: " + live_question.answer)
    question_is_live = False
    current_wager = 0
    # prep for /next route if someone wants the same category for next question
    categorized_questions = Question.get_questions_by_category(live_question.category, Timer(time_limit, reset_timer))
    # generate new question
    live_question = Question(Question.get_random_question(), Timer(time_limit, reset_timer))


# load this in the background to speed up response time
live_question = Question(Question.get_random_question(), Timer(time_limit, reset_timer))


# TODO: have this return a private error message to the person executing slash command (USE EPHEMERAL MESSAGE)
def handle_payload(payload, response_url, request_channel):
    """
    formats and returns payload
    :param payload: json formatted payload to return to slack API
    :param response_url: where we send the payload
    :param request_channel: channel where the API request comes from
    :return: post payload if in correct channel, otherwise post wrong_channel_payload
    """
    if request_channel == channel:
        return post(response_url, dumps(payload))
    else:
        return post(response_url, dumps(wrong_channel_payload))


# Routes

# say hi!
@app.route('/hello', methods=['POST'])
def hello():
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    payload = {
        'text': 'Hello ' + host.create_user_address(user_name, user_id),
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


host = Host(slack_token, user_db)
judge = Judge()


# display help text
@app.route('/howtoplay', methods=['POST'])
def howtoplay():
    payload = {
        'text': host.help_text,
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# display latest changelog
@app.route('/changelog', methods=['POST'])
def changelog():
    payload = {
        'text': host.get_latest_changelog('README.md'),
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# display uptime for trebekbot
@app.route('/uptime', methods=['POST'])
def uptime():
    payload = {
        'text': 'uptime: ' + host.uptime,
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# trebekbot asks a question
@app.route('/ask', methods=['POST'])
def ask():
    global live_question
    global daily_double_asker
    global question_is_live
    payload = {'text': None, 'response_type': 'in_channel'}
    # check if question has active timer
    if not question_is_live:
        if live_question.daily_double:
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
        # start question timer and double check that timer hasn't been started already
        if not live_question.timer.is_alive():
            live_question.timer.start()
        question_is_live = True
    else:
        payload['text'] = 'question is already in play!'
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)

# answer the current question
@app.route('/whatis', methods=['POST'])
def whatis():
    global live_question
    global daily_double_asker
    global current_wager
    global question_is_live
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    answer = request.form['text']
    payload = {'text': None, 'response_type': 'in_channel'}
    # if someone else tries to answer daily double
    if live_question.daily_double and user_name != daily_double_asker:
        payload['text'] = 'Not your daily double!'
    # if someone tries to answer daily double without wagering
    elif live_question.daily_double and not current_wager:
        payload['text'] = 'Please wager something first (not zero!).'
    elif not answer:
        payload['text'] = 'Please type an answer.'
    else:
        # delegate answer check to background worker
        answer_thread = Thread(target=answer_check_worker, args=[
            answer,
            user_name,
            user_id
        ])
        answer_thread.start()
        payload['text'] = 'Judges?'
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return jsonify({'text': answer, 'response_type': 'in_channel'})


# get a new question from the last question's category
@app.route('/next', methods=['POST'])
def next_question():
    global live_question
    global categorized_questions
    if request.form['channel_name'] == channel:
        # make sure that the next question isn't the same as the one we just asked
        if categorized_questions and live_question.slack_text != categorized_questions[0].slack_text:
            live_question = categorized_questions.pop()
            return Response(status=200), ask()
        else:
            say(channel, 'Out of that category! Here\'s a new question:')
            return Response(status=200), ask()


# forces skip on current question and generates new question
@app.route('/skip', methods=['POST'])
def skip():
    global live_question
    global daily_double_asker
    # cancel current timer and instantiate new question
    live_question.timer.cancel()
    live_question = Question(Question.get_random_question(), Timer(time_limit, reset_timer))
    payload = {'text': None, 'response_type': 'in_channel'}
    if live_question.daily_double:
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
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# get wager for daily double
@app.route('/wager', methods=['POST'])
def wager():
    global current_wager
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    current_wager = int(request.form['text'])
    payload = {
        'text': host.get_wager(current_wager, user_name, user_id),
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# pass daily double if user doesn't know answer
@app.route('/nope', methods=['POST'])
def nope():
    global current_wager
    global live_question
    global question_is_live
    payload = {
        'text': 'Coward. The correct answer is ' + live_question.answer,
        'response_type': 'in_channel'
    }
    if current_wager:
        payload['text'] = 'You can\'t pass if you\'ve already wagered!'
    if not live_question.daily_double:
        payload['text'] = 'Question must be a daily double!'
    else:
        live_question.timer.cancel()
        live_question = Question(Question.get_random_question(), Timer(time_limit, reset_timer))
        question_is_live = False
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# get user's score
@app.route('/myscore', methods=['POST'])
def myscore():
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    payload = {
        'text': host.my_score(user_name, user_id),
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# get user's tally of all-time wins
@app.route('/mywins', methods=['POST'])
def mywins():
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    payload = {
        'text': host.my_wins(user_name, user_id),
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# get list of all users' scores
@app.route('/topten', methods=['POST'])
def topten():
    payload = {
        'text': host.top_ten(),
        'response_type': 'in_channel'
    }
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# DEBUG Routes

# re-prints current question
@app.route('/current_question', methods=['POST'])
def current_question():
    global live_question
    payload = {'text': live_question.slack_text, 'response_type': 'in_channel'}
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# used to force a daily double for testing
@app.route('/dd', methods=['POST'])
def dd():
    global live_question
    global daily_double_asker
    payload = {'text': None, 'response_type': 'in_channel'}
    if request.form['user_name'] == 'bertrand_hustle':
        live_question = Question(Question.get_random_question(), Timer(time_limit, reset_timer))
        live_question.daily_double = True
        user_name = request.form['user_name']
        user_id = request.form['user_id']
        payload['text'] = live_question.slack_text
        payload['text'] += '\n' + host.create_daily_double_address(
            user_name, user_id
        )
        daily_double_asker = user_name
        # TODO: add time to timer if daily double
        live_question.timer.start()
        Thread(target=handle_payload,
               args=[payload, request.form['response_url'], request.form['channel_name']]).start()
        return Response(status=200)


# force crash/restart trebekbot
# TODO: make this cause a restart, right now it just throws a 500 error
@app.route('/crash', methods=['POST'])
def crash():
    if request.form['user_name'] == 'bertrand_hustle':
        raise Exception


# shows debug info
@app.route('/debug', methods=['POST'])
def debug():
    global live_question
    global question_is_live
    global current_wager
    debug_text = '''
    question = {}
    answer = {}
    question is_alive = {}
    question live = {}
    current_wager = {}
    '''.format(
        live_question.slack_text,
        live_question.answer,
        live_question.timer.is_alive(),
        question_is_live,
        current_wager
    )
    payload = {
        'text': debug_text,
        'response_type': 'in_channel'
    }
    print(request.form)
    # if request.form['user_name'] == 'bertrand_hustle':
    Thread(target=handle_payload,
           args=[payload, request.form['response_url'], request.form['channel_name']]).start()
    return Response(status=200)


# NOTE: set WEB_CONCURRENCY=1 to stop duplication problem
if __name__ == '__main__':
    # start main game
    app.run_server(debug=False, use_reloader=False)
    # app.run()
