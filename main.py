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
channel = '#trebektest'
# this needs to be outside the loop so it stays persistant
question_asked = None
answer_given = None

if __name__=='__main__':
    host = host.Host(slack_client)
    while True:
        # print rolling slack output to cmd
        slack_output = slack_client.rtm_read()
        print(slack_output)
        # main functions
        host.hello(slack_output)
        # this is how we store a persistant question
        current_question = host.ask_question(slack_output)
        if current_question:
            question_asked = q
        if question_asked:
            print(question_asked.text)
        answer_given = host.hear_answer(slack_output)
        print(answer_given)
        # logic for getting and checking question answers
        if question_asked and answer_given:
            host.check_answer(slack_output, question_asked)
        print('========================================')
        time.sleep(1)
