# Main file for trebekbot
# loosely based on this tutorial: https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
import os
import time
import host
from slackclient import SlackClient

author = 'bertrand_hustle'
bot_name = 'trebekbot'

# retrieve id/token/etc. from env variables
bot_id = os.environ.get('TREBEKBOT_ID')
slack_token = os.environ['TREBEKBOT_API_TOKEN']
slack_client = SlackClient(slack_token)
channel = '#general'
# this needs to be outside the loop so it stays persistant
# TODO: put in logic to reset these after answer
question_asked = None
answer_given = None

if __name__=='__main__':
    host = host.Host(slack_client)
    host.say(channel, host.help_text)
    while True:
        # print rolling slack output to cmd
        slack_output = slack_client.rtm_read()
        print(slack_output)
        # main functions
        host.hello(slack_output)
        host.help(slack_output)
        # this is how we store a persistant question
        current_question = host.ask_question(slack_output)
        print(current_question)
        if current_question:
            question_asked = current_question

        if question_asked:
            print(question_asked.text)

        current_answer = None
        if host.hear(slack_output, 'whatis'):
            current_answer = host.hear(slack_output, 'whatis')
        if current_answer:
            answer_given = current_answer

        print('GIVEN ANSWER')
        print(answer_given)

        # logic for getting and checking question answers
        if question_asked and answer_given:
            host.check_answer(slack_output, question_asked)
            question_asked = None
            answer_given = None
        print('========================================')
        time.sleep(1)
