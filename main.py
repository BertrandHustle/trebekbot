# Main file for trebekbot
# loosely based on this tutorial: https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
import os
import sys
import time
import host
import db
import question
from slackclient import SlackClient
from contextlib import suppress
from math import ceil

# TODO: make a setup.py file including editdistance and slackclient

author = 'bertrand_hustle'
bot_name = 'trebekbot'
build_version = '0.3'

# retrieve id/token/etc. from env variables
bot_id = os.environ.get('TREBEKBOT_ID')
slack_token = os.environ['TREBEKBOT_API_TOKEN']
slack_client = SlackClient(slack_token)
channel = '#trebektest'
# this needs to be outside the loop so it stays persistant
question_asked = None
answer_given = None
# timeout for questions
timer = 0
# time limit for questions
time_limit = 60
# used to measure when we should do our nightly restart
program_start_time = time.time()
# this translates to 24 hours
restart_offset = 86400
# vars for daily doubles
wager = 0
# this is who asked the daily double
daily_double_answerer = None

#TODO: impliment timeout on questions
if __name__=='__main__':
    # create host object
    host = host.Host(slack_client)
    # setup database
    user_db = db.db('users.db')
    user_db.create_table_users(user_db.connection)
    # host introduces itself to channel
    host.say(channel, host.help_text)

    while True:
        # get rolling slack output
        slack_output = slack_client.rtm_read()
        # main functions
        host.hello(slack_output)
        host.help(slack_output)
        host.myscore(slack_output, user_db)
        host.top_ten(slack_output)

        # this is how we store a persistant question/answer
        current_question = host.ask_question(slack_output)

        if current_question:
            question_asked = current_question
            # reset the timer when we ask for a new question
            timer = time.time()
            if current_question.daily_double:
                daily_double_answerer = host.get_user(slack_output[0])
                host.say(channel, 'It\'s a DAILY DOUBLE!')
                host.say(channel, '@'+daily_double_answerer+\
                ' Please enter a wager by typing ..wager <your wager>')

        # TODO: shorten timer for these questions
        # Daily Double control flow
        if question_asked and question_asked.daily_double:
            # try even if we don't have output
            with suppress(IndexError, KeyError):
                current_contestant = host.get_user(slack_output[0])
            # make sure that no one else gets to do the wagering
            if host.hear(slack_output, 'wager') and \
            current_contestant == daily_double_answerer:
                wager = host.get_wager(slack_output)
                host.say(channel, '@'+daily_double_answerer+', you\'ve \
                wagered '+str(wager))
            '''
            we need to check two things before someone can answer
            a daily double:
            1. are they the person who asked for it?
            2. have they entered in a wager?
            '''
            if host.hear(slack_output, 'whatis') and \
            current_contestant == daily_double_answerer and \
            wager:
                host.check_answer(slack_output, question_asked)
                # reset the question/answer
                question_asked = None
                answer_given = None
            # need to make sure we have a wager first
            elif host.hear(slack_output, 'whatis') and not wager:
                host.say(channel, 'Please enter a wager first.')

        current_answer = None
        if host.hear(slack_output, 'whatis') and question_asked \
        and not question_asked.daily_double:
            current_answer = host.hear(slack_output, 'whatis')
        if current_answer:
            answer_given = current_answer

        # logic for getting and checking question answers
        if question_asked and answer_given and question_asked \
        and not question_asked.daily_double:
            if host.check_answer(slack_output, question_asked):
                # reset the question/answer
                question_asked = None
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
        current_time = time.time()
        if question_asked and time.time() >= timer + time_limit:
            host.say(channel, "Sorry, we're out of time. The correct answer is: " + question_asked.answer)
            # we want to take points away if it's a daily double
            if question_asked.is_daily_double:
                user_db.update_score(user_db.connection, \
                daily_double_answerer, -wager)
            question_asked = None
            answer_given = None

        # check when to restart trebekbot nightly
        if current_time >= program_start_time + restart_offset:
            host.say(channel, 'Restarting!')
            # store the current champ so we can recall it after restart
            champion_name, champion_score = db.get_champion(user_db)
            champion_file = open('./support_files/champion.txt', 'w')
            champion_file.write(champion_name)
            champion_file.write(champion_score)
            champion_file.close()
            # restart trebekbot
            os.execv(sys.executable, ['python'] + sys.argv)

        # printing for debug purposes
        print(slack_output)
        if question_asked:
            print('QUESTION: '+question_asked.text)
            print('ANSWER: '+question_asked.answer)
        if answer_given:
            print('GIVEN ANSWER: ' + answer_given)
        print('========================================')
        print('TIMER: ' + str(timer))
        # delay so trebekbot has time to think
        print('DAILY DOUBLE DEBUGGING')
        print(daily_double_answerer)
        print(wager)
        time.sleep(1)
