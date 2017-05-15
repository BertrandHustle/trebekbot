# Main file for trebekbot
# loosely based on this tutorial: https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
import os
import time
from slackclient import SlackClient

# retrieve id/token/etc. from env variables
'''
bot_id = os.environ.get('BOT_ID')
slack_token = os.environ["SLACK_API_TOKEN"]
'''

# TODO: call this as env variable (see above), fix KeyError: SLACK_BOT_TOKEN
slack_token = 'xoxb-183776207538-bVt3eahGLLMLmaEjzUkMNi4O'
sc = SlackClient(slack_token)

author = 'bertrand_hustle'
bot_name = 'trebekbot'

sc.api_call(
    'chat.postMessage',
    channel='#trebektest',
    text='Hi Lana!'
)
print('test')

'''
if __name__ == "__main__":
    # 1 second delay between reading from firehose
    READ_WEBSOCKET_DELAY = 1
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
'''
