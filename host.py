import main
import question
import db
from re import sub
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
    ;;whatis: use this to provide an answer to the question
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
            # prefix without the ';;'
            prefix = text[2:].split(' ')[0]
            # if the text starts with the command_prefix
            # and the rest of the text minus the prefix matches what we're listening for
            if text.startswith(self.command_prefix) \
            and prefix == listen_for:
                answer = text.split(prefix)[1]
                if answer:
                    # return the answer without the prefix if we 'hear' the command prefix
                    return answer
                else:
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
            user = self.get_user(slack_output)
            self.say(main.channel, 'Hello @'+user)

    # gets a random question from the jeopardy_json_file
    # TODO: make this scrub out html links
    def ask_question(self, slack_output):
        if self.hear(slack_output, 'ask'):
            # slack_output = slack_output[0]
            asked_question = question.Question()
            # parse this so it's pretty in slack
            question_text = '[*'+asked_question.category+'*] ' + '['+asked_question.get_value()+'] ' + '_'+asked_question.text+'_'
            self.say(main.channel, question_text)
            return asked_question

    def check_answer(self, slack_output, question):
        if self.hear(slack_output, 'whatis'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            user_answer = slack_output['text'].split('whatis')[1]
            correct_answer = question.answer
            print('CORRECT ANSWER')
            print(correct_answer)
            print('USER ANSWER')
            print(user_answer)
            if self.fuzz_answer(user_answer, correct_answer):
                self.say(main.channel, 'That is correct.')
                # TODO: update user's score with question.value
                return user
            else:
                self.say(main.channel, 'Sorry, that is incorrect.  The correct answer was '+correct_answer)
                return user

    # TODO: add ;;top to return top 10 scorers
    # TODO: add ;;myscore to help text

    # returns user's current score
    def myscore(self, slack_output, db):
        if self.hear(slack_output, 'myscore'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            self.say(main.channel, 'Your score is: '+db.return_score(db.connection, user))

    '''
    checks if given answer is close enough to the right answer by doing the following:
    1. remove casing
    2. remove whitespace
    3. check if an acceptable fraction of the letters are correct
    '''
    @staticmethod
    def fuzz_answer(given_answer, correct_answer):
        if type(given_answer) != str:
            return False
        # check for empty strings e.g. ''
        elif not ''.join(given_answer.lower().split()).isalnum():
            return False
        else:
            # remove casing and whitespace
            # thanks to Ants Aasma on stack overflow for this solution
            given_answer = sub(r'\W+', '', given_answer).lower()
            correct_answer = sub(r'\W+', '', correct_answer).lower()
            # count how many mismatched letters we have
            error_count = 0
            error_ratio = len(correct_answer)/8
            paired_letters = list(zip(given_answer, correct_answer))
            for first_letter, second_letter in paired_letters:
                if first_letter != second_letter:
                    error_count += 1
            if error_count <= error_ratio:
                return True
            else:
                return False
