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
# set to 1 for debug mode
debug = 0
# retrieve id/token/etc. from env variables
# bot_id = os.environ.get('TREBEKBOT_ID')
slack_token = os.environ['TREBEKBOT_API_TOKEN']
slack_client = SlackClient(slack_token)
# NOTE: do not use # in the name, slack's api returns the channel name only
channel = 'trivia'
# export channel to env so host can grab it
os.environ['SLACK_CHANNEL'] = channel
# this needs to be outside the loop so it stays persistant
question_asked = None
answer_given = None
# timeout for questions
timer = 0
# time limit for questions
time_limit = 60
# vars for daily doubles
wager = 0
# this is who asked the daily double
daily_double_answerer = None
# tracking last night's champion
current_champion_name = None
current_champion_score = None

@app.route('/ask', methods=['POST'])
def ask():
    if request.form['token'] == os.environ['SIGNING_SECRET']:
        question_asked = question.Question()
        payload = {'text' : question_asked.slack_text}
        payload = jsonify(payload)
        payload.status_code = 200
        return payload
    else:
        return request.form

@app.route('/ask_test', methods=['POST'])
def ask_test():
    question_asked = question.Question()
    return jsonify(question.Question().slack_text)

# TODO: get rid of all champion_score functions and db columns
if __name__=='__main__':
    app.run()
    # create host object
    host = host.Host(slack_client, user_db)
    # host introduces itself to channel
    host.say(channel, host.intro_text)
    host.say(channel, host.help_text)
    # establish champion
    current_champion_name, current_champion_score = host.current_champion_name,\
    host.current_champion_score
    # announce champ
    if current_champion_name and current_champion_score > 0:
        # add a win to the user's all-time win count
        user_db.increment_win(user_db.connection, current_champion_name)
        host.say(channel, 'Let\'s welcome back last night\'s returning champion, \
        :crown: @' + current_champion_name + '!')
        host.say(channel, 'With a total cash winnings of '+ \
        '$' + str(current_champion_score) + '!')
    # show yesterday's leaderboard
    host.say(channel, 'Here\'s yesterday\'s top scores:')
    host.top_ten(slack_output='', force=1)
    # reset champion_scores here
    user_db.wipe_scores(user_db.connection)

    while True:
        # get rolling slack output
        slack_output = slack_client.rtm_read()
        # main functions
        host.hello(slack_output)
        host.help(slack_output)
        host.myscore(slack_output, user_db)
        host.top_ten(slack_output)
        host.changelog(slack_output)
        host.say_uptime(slack_output)
        host.mywins(slack_output)
        # used for debugging purposes
        host.crash(slack_output)
        # TODO impliment debug daily double here

        #TODO: change this so it always has a waiting question to be asked
        current_question = host.ask_question(slack_output)

        if current_question:
            # this is how we store a persistant question/answer
            question_asked = current_question
            # reset the timer when we ask for a new question
            timer = time.time()

            # check for daily double
            if question_asked.daily_double:
                daily_double_answerer = host.get_user(slack_output[0])
                daily_double_answerer_score = \
                user_db.get_score(user_db.connection, daily_double_answerer)
                # we need a little extra time to put in a wager and answer
                daily_double_timer = time.time() + 30
                host.say(channel, 'It\'s a DAILY DOUBLE!')
                host.say(channel, '@'+daily_double_answerer+' [$'+str(daily_double_answerer_score)+'] ' \
                + ' Please enter a wager by typing ..wager <your wager>')

                # TODO: shorten timer for these questions
                # Daily Double control flow
                while question_asked and question_asked.daily_double:
                    # get rolling slack output
                    slack_output = slack_client.rtm_read()
                    # try even if we don't have output
                    with suppress(IndexError, KeyError):
                        current_contestant = host.get_user(slack_output[0])
                    # pass if contestant doesn't know answer
                    if host.hear(slack_output, 'nope'):
                        if not wager:
                            host.say(channel, "Coward. The correct answer is: "\
                            + question_asked.answer)
                            # this breaks out of loop
                            question_asked, answer_given, wager = None, None, None
                        else:
                            host.say(channel, "Sorry, you cannot pass after wagering.")
                    # make sure that no one else gets to do the wagering
                    if host.hear(slack_output, 'wager') and \
                    current_contestant == daily_double_answerer:
                        wager = host.get_wager(slack_output, daily_double_answerer_score)
                        host.say(channel, '@'+daily_double_answerer + \
                        ', you\'ve wagered $'+str(wager))
                    '''
                    we need to check two things before someone can answer
                    a daily double:
                    1. are they the person who asked for it?
                    2. have they entered in a wager?
                    '''
                    if host.hear(slack_output, 'whatis') and \
                    current_contestant == daily_double_answerer and \
                    wager:
                        daily_double_answer = host.check_answer(slack_output, question_asked, wager)
                        # wrong answer
                        if not daily_double_answer:
                            # reset the question/answer and break out of loop
                            host.say(channel, "Sorry, the correct answer is: " + question_asked.answer)
                            question_asked, answer_given, wager = None, None, None
                        # right answer
                        elif daily_double_answer is 'right':
                            question_asked, answer_given, wager = None, None, None
                    # need to make sure we have a wager first
                    elif host.hear(slack_output, 'whatis') and not wager:
                        host.say(channel, 'Please wager something first (not zero!).')
                    # keep track of time
                    if time.time() >= daily_double_timer + time_limit:
                        host.say(channel, "Sorry, we're out of time. The correct answer is: " + question_asked.answer)
                        if wager:
                            user_db.update_score(user_db.connection, \
                            daily_double_answerer, -wager)
                        question_asked, answer_given, wager = None, None, None

        # this needs to only be set if we hear 'whatis' so we don't attempt to
        # parse blank answers
        current_answer = None
        # TODO: fix this so it uses 'whois' too
        if host.hear(slack_output, 'whatis') and question_asked \
        and not question_asked.daily_double:
            current_answer = host.hear(slack_output, 'whatis')
        if current_answer:
            answer_given = current_answer

        # logic for getting and checking question answers
        if question_asked and answer_given:
            # the results of checking whether the answer is right
            answer_check_result = host.check_answer(slack_output, question_asked)
            # if answer is right
            if answer_check_result == 'right':
                answer_given = None
                question_asked = None
            # we want to only wipe the answer so other people can guess if
            # answer is close or wrong
            # TODO: make this so an individual can only answer once
            elif answer_check_result:
                answer_given = None
        # having an answer_given stored without a question can lead to
        # trebekbot becoming unable to be asked questions, so we need
        # to make sure that if there's an answer stored without a question,
        # we wipe them both
        elif answer_given and not question_asked:
            question_asked = None
            answer_given = None
        else:
            pass

        # only check the timer if there's an active question
        if question_asked and time.time() >= timer + time_limit:
            host.say(channel, "Sorry, we're out of time. The correct answer is: " + question_asked.answer)
            # we want to take points away if it's a daily double
            if question_asked.is_daily_double and wager:
                user_db.update_score(user_db.connection, \
                daily_double_answerer, -wager)
            question_asked = None
            answer_given = None

        '''
        current_time = datetime.now().time()
        if current_time.hour == 11 and current_time.minute == 59 and current_time.second == 59:
            host.say(channel, 'Tonight\'s Top Scorers:')
            host.top_ten(slack_output, force=1)
            host.say(channel, 'Restarting!')
            # set the current champion in our database
            champion_name, champion_score = \
            user_db.get_champion(user_db.connection)
            if champion_name:
                user_db.set_champion(user_db.connection, champion_name, champion_score)
            # make sure scores are reset when bot resets
            user_db.wipe_scores(user_db.connection)
            # restart trebekbot
            os.execv(sys.executable, ['python'] + sys.argv)
        '''

        # printing for debug purposes
        if debug:
            test_slack_output = [{'text': '..ask', 'ts': '1528073804.000085', 'channel': 'C600FK4T1', 'user': 'U5ZVBSBE2', 'type': 'message', 'team': 'T5YF6LB9N', 'source_team': 'T5YF6LB9N'}]
            print(slack_output)
            if question_asked:
                print('QUESTION: '+question_asked.text)
                print('ANSWER: '+question_asked.answer)
            if answer_given:
                print('GIVEN ANSWER: ' + answer_given)
            print('========================================')
            print('TIMENOW: ' + str(round(time.time()%60)))
            print('TIMER + TIME LIMIT: ' + str(round(timer%60) + 60))
            print(current_champion_name)
        # delay so trebekbot has time to think
        time.sleep(1)
