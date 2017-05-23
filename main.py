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

if __name__=='__main__':
    host = host.Host(slack_client)
    while True:
        # print rolling slack output to cmd
        slack_output = slack_client.rtm_read()
        print(slack_output)
        host.hello(slack_output)
        print('========================================')
        time.sleep(1)
