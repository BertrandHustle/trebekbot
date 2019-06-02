author = 'bertrand_hustle'
bot_name = 'trebekbot'

# Main file for trebekbot
import sys
import os
import src.question as question
import src.db as db
import src.host as host
import time
import urllib.parse as urlparse
from threading import Timer
from datetime import datetime
from slackclient import SlackClient
from contextlib import suppress
from flask import Flask, jsonify, request

app = Flask(__name__)

# set to 1 for debug mode
debug = 0
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
# this needs to be outside the loop so it stays persistant
question_asked = question.Question()
# time limit for questions
time_limit = 60
# vars for daily doubles
wager = 0
# this is who asked the daily double
daily_double_answerer = None

# resets timer and removes active question and answer
def reset_timer():
    global question_asked
    host.say(channel, "Sorry, we're out of time. The correct answer is: " + question_asked.answer)
    # generate new question
    question_asked = question.Question()
    # timers can only be started once so we need to make a new one
    timer = Timer(time_limit, reset_timer)

timer = Timer(time_limit, reset_timer)

# trebekbot asks a question
@app.route('/ask', methods=['POST'])
def ask():
    payload = {
    'text' : question_asked.slack_text,
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    # start question timer
    timer.start()
    return payload

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

# TODO: figure out why this isn't taking the user answer
# answer the current question
@app.route('/whatis', methods=['POST'])
def whatis():
    global question_asked
    user_name = request.form['user_name']
    user_id = request.form['user_id']
    answer = request.form['text']
    answer_check = host.check_answer(question_asked, answer, user_name, user_id)
    payload = {
    'text' : answer_check,
    'response_type' : 'in_channel'
    }
    payload = jsonify(payload)
    payload.status_code = 200
    # if answer is correct we need to reset timer and make new questions
    if ':white_check_mark:' in answer_check:
        question_asked = question.Question()
        reset_timer()
    return payload

# TODO: get rid of all champion_score functions and db columns
if __name__=='__main__':
    # start main game
    # app.run(debug=False, use_reloader=False)
    app.run()
    # question timer, has to be created after reset_timer
