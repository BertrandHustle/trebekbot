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
answer_given = None
# time limit for questions
time_limit = 60
# vars for daily doubles
wager = 0
# this is who asked the daily double
daily_double_answerer = None
# init so we can declare these later in main and not break heroku
host = None
timer = Timer(time_limit, reset_timer)

# resets timer and removes active question and answer
def reset_timer():
    host.say(channel, "Sorry, we're out of time. The correct answer is: " + question_asked.answer)
    # we want to take points away if it's a daily double
    if question_asked.is_daily_double and wager:
        user_db.update_score(user_db.connection, \
        daily_double_answerer, -wager)
    # generate new question
    question_asked = question.Question()
    answer_given = None

# trebekbot asks a question
@app.route('/ask', methods=['POST'])
def ask():
    payload = {
    'text' : question_asked.slack_text,
    'response_type' : 'in_channel'}
    payload = jsonify(payload)
    payload.status_code = 200
    # start question timer
    timer.start()
    return payload

# say hello to a user
@app.route('/hello', methods=['POST'])
def hello():
    user = request.form['user_name']
    payload = {
    'text' : 'Hello ' + user,
    'response_type' : 'in_channel'}
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# display help text
@app.route('/help', methods=['POST'])
def help():
    payload = {
    'text' : host.help_text,
    'response_type' : 'in_channel'}
    payload = jsonify(payload)
    payload.status_code = 200
    return payload

# TODO: get rid of all champion_score functions and db columns
if __name__=='__main__':
    # start main game
    # app.run(debug=False, use_reloader=False)
    app.run()
    # create host object
    # host = host.Host(slack_client, user_db)
    # question timer, has to be created after reset_timer
