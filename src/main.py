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
from time import sleep

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
# load this in the background to speed up response time
banked_question = question.Question()
# this needs to be outside the loop so it stays persistant
live_question = None
# time limit for questions
time_limit = 60
# vars for daily doubles
wager = 0
# this is who asked the daily double
daily_double_answerer = None
# question timer
timer = Timer(time_limit, reset_timer)

# resets timer and removes active question and answer
def reset_timer():
    global banked_question
    global live_question
    global timer
    host.say(channel, "Sorry, we're out of time. The correct answer is: " + live_question.answer)
    # generate new question
    banked_question = question.Question()
    # wipe out live question
    live_question = None
    # timers can only be started once so we need to make a new one
    timer = Timer(time_limit, reset_timer)

# say hello to a user
@app.route('/hello', methods=['POST'])
def hello():
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
@app.route('/help', methods=['POST'])
def help():
    payload = {
    'text' : host.help_text,
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# TODO: implement sleep here?
# trebekbot asks a question
@app.route('/ask', methods=['POST'])
def ask():
    global live_question
    payload = {'text': None, 'response_type': 'in_channel'}
    # if we don't already have a live question
    if not live_question:
        live_question = banked_question
        payload['text'] = live_question.slack_text
        # start question timer
        timer.start()
    else:
        payload['text'] = 'question is already in play!'
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# answer the current question
@app.route('/whatis', methods=['POST'])
def whatis():
    global question_asked
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    answer = request.form['text']
    answer_check = host.check_answer(live_question, answer, user_name, user_id)
    payload = {
    'text' : answer_check,
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    # if answer is correct we need to reset timer and make new questions
    if ':white_check_mark:' in answer_check:
        timer.cancel()
    return payload

if __name__=='__main__':
    # start main game
    # app.run(debug=False, use_reloader=False)
    app.run()
