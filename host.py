import main
import question
import db
from re import sub
from contextlib import suppress

# initialize user database
user_db = db.db('users.db')

'''
 Class that acts as the "host" of Jeopardy
 e.g. asks clues, gets point values, etc.
 think of this as the class that handles listening and talking to slack
'''

class Host:

    # what to type before we give trebekbot a command
    command_prefix = '..'
    help_text = '''
    This iiiiiis trebekbot!

    Use '''+command_prefix+''' to prefix commands.
    '''+command_prefix+'''help: bring up this help list
    '''+command_prefix+'''hello: say hello to trebekbot
    '''+command_prefix+'''ask: trebekbot will ask you a question
    '''+command_prefix+'''whatis: use this to provide an answer to the question
    '''+command_prefix+'''myscore: find out what your current score is
    '''+command_prefix+'''topten: find out who the top ten scorers are
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

    def hear(self, slack_output, listen_for):
        with suppress(IndexError, KeyError):
            # for some reason slack's output is a dict within a list, this gives us just the list
            slack_output = slack_output[0]
            text = slack_output['text']
            user = self.get_user(slack_output)
            # prefix without the ';;'
            prefix = text[2:].split(' ')[0]
            # if the text starts with the command_prefix
            # and the rest of the text minus the prefix matches what we're listening for
            if text.startswith(self.command_prefix) \
            and prefix == listen_for:
                answer = text.split(prefix)[1]
                user_db.add_user_to_db(user_db.connection, user)
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
            asked_question = question.Question()
            # parse this so it's pretty in slack
            question_text = '[*'+asked_question.category+'*] ' + '['+asked_question.get_value()+'] ' + '_'+asked_question.text+'_'
            self.say(main.channel, question_text)
            return asked_question

    # TODO: change this to /what /who for mobile users
    def check_answer(self, slack_output, question):
        if self.hear(slack_output, 'whatis'):
            # this drills down into the slack output to get the given answer
            slack_output = slack_output[0]
            user_answer = slack_output['text'].split('whatis')[1]
            # who asked the question
            user = self.get_user(slack_output)
            user_id = slack_output['user']
            correct_answer = question.answer
            print('CORRECT ANSWER')
            print(correct_answer)
            print('USER ANSWER')
            print(user_answer)
            # TODO: add :x: and :white_check_mark: emojis, and repond to user
            # with @user
            if self.fuzz_answer(user_answer, correct_answer):
                self.say(main.channel, '<@'+user_id+'|'+user+'>'+ ' :white_check_mark: That is correct.')
                # award points to user
                user_db.update_score(user_db.connection, user, question.value)
                return user
            else:
                self.say(main.channel, '<@'+user_id+'|'+user+'>'+ ' :x: Sorry, that is incorrect.  The correct answer was '+correct_answer)
                # take away points from user
                user_db.update_score(user_db.connection, user, -question.value)
                return user

    # returns user's current score
    def myscore(self, slack_output, db):
        if self.hear(slack_output, 'myscore'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            self.say(main.channel, 'Your score is: '+ ' $' + str(db.return_score(db.connection, user)))

    # returns top ten scorers
    def top_ten(self, slack_output):
        if self.hear(slack_output, 'topten'):
            top_ten_list = user_db.return_top_ten(user_db.connection)
            slack_list = 'Here\'s our top scorers: \n'
            count = 1
            for id,name,score in top_ten_list:
                # format: 1. Morp - $501
                slack_list += str(count) + '. ' + name + ' - ' + '$' \
                + str(score) + '\n'
                count += 1
            self.say(main.channel, slack_list)

    # allows contestants to bet on daily doubles
    def daily_double(self, slack_output):
        if self.hear(slack_output, 'wager'):
            # format: <wager>|<answer>
            slack_output = slack_output[0]
            try:
                split_on_pipe = slack_output.split('|')
                wager = split_on_pipe[0]
                answer = split_on_pipe[1]
                # in case we get $2,000 instead of 2000
                if type(wager) == 'str':
                    wager = Question.convert_value_to_int(wager)
                return (wager, answer)
            except IndexError:
                self.say(main.channel, 'Please answer in the correct format:\
                answer|wager')

    # strips answers of extraneous punctuation, whitespace, etc.
    @staticmethod
    def strip_answer(answer):
        '''
        remove casing, we also prefix a space so the next regex will
        catch articles that start the string (otherwise we'd need a
        '^' in addition to a '\s')
        '''
        answer = ' ' + answer.lower()
        # remove articles and conjunctions
        answer = sub(r'\sand\s|\sthe\s|\san\s|\sa\s', '', answer)
        # remove anything that's not alphanumeric
        answer = sub(r'[^A-Za-z0-9]', '', answer)
        return answer


    '''
    checks if given answer is close enough to the right answer by doing the following:
    1. remove casing
    2. remove whitespace
    3. check if an acceptable fraction of the letters are correct
    '''

    '''
    1. every time there's a match, remove the pair
    2. when we reach a pair that doesn't match, see if the first
    word is a big enough substring of the second
    infintesimal
    infinitesimal

    esimal
    tesimal
    '''

    @staticmethod
    def fuzz_answer(given_answer, correct_answer):
        if type(given_answer) != str or type(correct_answer) != str:
            return False
        else:
            # remove casing, whitespace, punctuation, and articles
            print (given_answer)
            print (correct_answer)
            given_answer = Host.strip_answer(given_answer)
            correct_answer = Host.strip_answer(correct_answer)
            print (given_answer)
            print (correct_answer)
            # count how many mismatched letters we have
            error_count = 0
            error_ratio = len(correct_answer)/8
            paired_letters = list(zip(given_answer, correct_answer))
            for first_letter, second_letter in paired_letters:
                if first_letter != second_letter:
                    error_count += 1
            '''
            check if paired_letters is empty, e.g. []
            this happens if we pass in an empty string ('')
            '''
            if paired_letters and error_count <= error_ratio:
                return True
            else:
                return False
