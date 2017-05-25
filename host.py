import main
import question
from contextlib import suppress

'''
 Class that acts as the "host" of Jeopardy
 e.g. asks clues, gets point values, etc.
 think of this as the class that handles listening and talking to slack
'''

class Host:

    # what to type before we give trebekbot a command
    command_prefix = ';;'
    help_text = '''
    This iiiiiis trebekbot!
    Use ;; to prefix commands.
    ;;help: bring up this help list
    ;;hello: say hello to trebekbot
    ;;ask: trebekbot will ask you a question
    ;;whatis: use this to provide an answer to the quetion
    '''

    def __init__(self, slack_client):
        self.slack_client = slack_client
        # connect to slack upon init
        slack_client.rtm_connect()

    # listens for output in slack channel
    '''
    output example:
    [{'ts': '1495558884.473102',
    'source_team': 'T5G5Z47RN',
    'text': 'LOOK',
    'user': 'U5G8Y4H89',
    'team': 'T5G5Z47RN',
    'type': 'message',
    'channel': 'C5HLVN346'}]
    '''

    # unsure why it passes the Host object in as well, but that's why 'self' is needed here
    def hear(self, slack_output, listen_for):
        with suppress(IndexError, KeyError):
            # for some reason slack's output is a dict within a list, this gives us just the list
            slack_output = slack_output[0]
            text = slack_output['text']
            # if the text starts with the command_prefix
            # and the rest of the text minus the prefix matches what we're listening for
            if text.startswith(self.command_prefix) \
            and text[2:].split(' ')[0] == listen_for:
                # return True if we 'hear' the command prefix
                return True

    # say things back to channel
    '''
    :param: channel: channel to which we are posting message
    :param: message: message to post or 'say'
    '''
    def say(self, channel, message):
        self.slack_client.api_call(
            'chat.postMessage',
            channel=channel,
            text=message,
            as_user=True
        )

    # get user by checking user id
    def get_user(self, slack_output):
        user_id = slack_output['user']
        user = self.slack_client.api_call(
        'users.info',
        user=user_id
        )
        return user['user']['name']

    # COMMANDS

    # lists trebekbot functions
    def help(self, slack_output):
        if self.hear(slack_output, 'help'):
            self.say(main.channel, self.help_text)

    # say hi!
    def hello(self, slack_output):
        if self.hear(slack_output, 'hello'):
            slack_output = slack_output[0]
            user = get_user(slack_output)
            self.say(main.channel, 'Hello @'+user)

    # gets a random question from the jeopardy_json_file
    def ask_question(self, slack_output):
        if self.hear(slack_output, 'ask'):
            # slack_output = slack_output[0]
            asked_question = question.Question()
            # parse this so it's pretty in slack
            question_text = '[*'+asked_question.category+'*] ' + '['+asked_question.get_value()+'] ' + '_'+asked_question.text+'_'
            self.say(main.channel, question_text)
            return asked_question

    # TODO: add logic to check who answered it
    # TODO: add algorithm for near-spelling
    def check_answer(self, slack_output, question):
        slack_output = slack_output[0]
        user = self.get_user(slack_output)
        user_answer = slack_output['text']
        correct_answer = question.answer
        # do lower to ensure that casing doesn't matter
        print(user_answer.lower(), question.answer.lower())
        # split and slice to get the actual answer
        if user_answer.lower()[2:].split(' ')[1] == question.answer.lower():
            self.say(main.channel, 'That is correct.')
            return True
        else:
            self.say(main.channel, 'Sorry, that is incorrect.  The correct answer was '+correct_answer)
