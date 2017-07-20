# Main file for trebekbot
# loosely based on this tutorial: https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
import os
import time
import host
import db
import question
from slackclient import SlackClient
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
        # time loops for debug purposes
        loop_start_time = time.time()
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
            timer = 0
            if current_question.daily_double:
                host.say(channel, 'It\'s a DAILY DOUBLE!')
                host.say(channel, 'Please enter a wager by typing ..wager <your wager>')
                print(host.get_wager(slack_output))
                wager, daily_double_answerer = host.get_wager(slack_output)
                # make sure only the person who got the daily double can answer
                if host.hear(slack_output, 'whatis') and \
                host.get_user(slack_output[0]) == daily_double_answerer:
                    host.check_answer(host.hear(slack_output, 'whatis'), question_asked)
                    # reset the question/answer
                    question_asked = None
                    answer_given = None

        current_answer = None
        if host.hear(slack_output, 'whatis') and not question_asked.daily_double:
            current_answer = host.hear(slack_output, 'whatis')
        if current_answer:
            answer_given = current_answer

        # logic for getting and checking question answers
        if question_asked and answer_given and not question_asked.daily_double:
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

        # timeout mechanism
        if question_asked:
            timer += 1
        if timer >= 120:
            host.say(channel, "Sorry, we're out of time. The correct answer is: " + question_asked.answer)
            # we want to take points away if it's a daily double
            if question_asked.is_daily_double:
                user_db.update_score(user_db.connection, \
                daily_double_answerer, -wager)
            question_asked = None
            answer_given = None
            timer = 0
        if not question_asked and not answer_given:
            timer = 0

        # printing for debug purposes
        print(slack_output)
        if question_asked:
            print('QUESTION: '+question_asked.text)
            print('ANSWER: '+question_asked.answer)
        if answer_given:
            print('GIVEN ANSWER: ' + answer_given)
        print('========================================')
        print(timer)
        # track time per loop for debugging
        print(round(time.time()-loop_start_time, 5))
        # delay so trebekbot has time to think
        time.sleep(1)
