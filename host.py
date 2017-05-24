import main
import json
from random import randint
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
            question = Question()
            # parse this so it's pretty in slack
            question_text = '[*'+question.category+'*] ' + '['+question.get_value()+'] ' + '_'+question.text+'_'
            self.say(main.channel, question_text)
            return question

    # listens for someone trying to answer a question
    def hear_answer(self, slack_output):
        if self.hear(slack_output, 'whatis'):
            return True

    # TODO: add logic to check who answered it
    # TODO: add algorithm for near-spelling
    def check_answer(self, slack_output, question):
        # if self.hear(slack_output, 'whatis'):
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

'''
Holds details about questions and questions themselves
:str text: The actual text of the question
:str answer: The answer to the question
:int value: The dollar value of the question
:str category: The category of the question
:boolean daily_double: True if question is a daily double
'''

class Question:
    def __init__(self):
        jeopardy_json_file = open('./csv_files/JEOPARDY_QUESTIONS1.json').read()
        question = json.loads(jeopardy_json_file)
        # json file has 216,930 questions
        question = question[randint(0, 216930)]
        self.text = question['question']
        self.value = self.convert_value_to_int(question['value'])
        self.category = question['category']
        self.daily_double = Question.is_daily_double(self.value)
        self.answer = question['answer']

    def get_value(self):
        return ('$' + str(self.value))

    def is_daily_double(value):
        if type(value) is str:
            int_value = int(value[1:])
            if int_value < 1:
                return 'Invalid Value'
            elif int_value > 2000 and int_value % 100 != 0:
                return True
            else:
                return False
        elif type(value) == int:
            if value < 1:
                return 'Invalid Value'
            elif value > 2000 and value % 100 != 0:
                return True
            else:
                return False

    # to remove $ and commas from question values, e.g. '$2,500'
    def convert_value_to_int(self, value):
        try:
            # remove special characters if this is a string
            if type(value) == str:
                # check for negative numbers that haven't been converted to int yet
                if '-' in value:
                    return 'Invalid Value'
                else:
                    value = ''.join(c for c in value if c.isalnum())
                    value = int(value)
            # check to make sure value is over $1
            # TODO: fix this to check for this error:
            # TypeError: unorderable types: NoneType() < int()
            if value < 1:
                return 'Invalid Value'
            else:
                return value
        except ValueError:
            return 'Invalid Value'

'''
def get_question():
    jeopardy_json_file = open('./csv_files/JEOPARDY_QUESTIONS1.json').read()
    question = json.loads(jeopardy_json_file)
    # json file has 216,930 questions
    question = question[randint(0, 216930)]
    text = question['question']
    value = int(question['value'][1:])
    category = question['category']
    daily_double = Question.is_daily_double(value)
    answer = question['answer']
    print(text, value, category, daily_double, answer)
    return Question(text, value, category, daily_double, answer)
'''
