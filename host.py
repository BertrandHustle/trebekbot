import main
import question
import db
from re import sub
from contextlib import suppress
import difflib

# initialize user database
user_db = db.db('users.db')
# initialize dictionary
# TODO: detect if os.name == linux, use /usr/bin/words if so
eng_dict = open('./json_files/words.txt').read().splitlines()

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
            # and we're in the right channel
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

    '''
    [{'source_team': 'T0LR9NXQQ', 'team': 'T0LR9NXQQ', 'text':
    'aw, he restarted', 'type': 'message', 'ts': '1497097067.238474',
    'user': 'U1UU5ARJ6', 'channel': 'C5LMQHV5W'}]
    '''

    def get_channel(self, slack_output):
        channel_id = slack_output['channel']
        channel = self.slack_client.api_call(
        'channels.info'
        )
        # add the hash to make it match the main.channel value
        return '#'+channel['channel']['name']

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
            answer_check = self.fuzz_answer(user_answer, correct_answer)

            print('CORRECT ANSWER')
            print(correct_answer)
            print('USER ANSWER')
            print(user_answer)

            if answer_check:
                self.say(main.channel, '<@'+user_id+'|'+user+'>'+ ' :white_check_mark: That is correct. The answer is ' +correct_answer)
                # award points to user
                user_db.update_score(user_db.connection, user, question.value)
                return 1
            # TODO: move this logic into fuzz_answer()
            elif answer_check is 'close':
                self.say(main.channel, '<@'+user_id+'|'+user+'>'+ ' Please be more specific.')
            else:
                self.say(main.channel, '<@'+user_id+'|'+user+'>'+ ' :x: Sorry, that is incorrect.  The correct answer was '+correct_answer)
                # take away points from user
                user_db.update_score(user_db.connection, user, -question.value)


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
        # check if
        if type(given_answer) != str \
        or type(correct_answer) != str \
        or not given_answer \
        or len(given_answer) < len(correct_answer)*0.8:
            return False
        else:

            '''
            for every word
            1. strip word
            2. if it == answer word or matches dict, True
            3. elif it is a big enough substring, close
            4. else: false
            '''

            # remove casing, whitespace, punctuation, and articles
            #given_answer = Host.strip_answer(given_answer)
            #correct_answer = Host.strip_answer(correct_answer)
            #print(given_answer, correct_answer)

            split_words = given_answer.split(' ')
            for word in split_words:
                # remove casing, whitespace, punctuation, and articles
                stripped_given_word = Host.strip_answer(given_answer)
                stripped_correct_word = Host.strip_answer(correct_answer)
                # print test
                print(stripped_given_word, stripped_correct_word)
                # use lambda to pare down dict
                first_letter_eng_dict = filter(lambda x: x[:1] == given_answer[:1], eng_dict)
                # get list of close words (spell check)
                check_word_closeness = difflib.get_close_matches \
                (given_answer, first_letter_eng_dict, n=5, cutoff=0.8)
                # print test
                print (check_word_closeness)
                # if it's in the spell check, it's correct
                if stripped_given_word not in check_word_closeness or \
                # check if the guessed word is a big enough substring of the correct word
                given_answer not in correct_answer \
                or len(given_answer) >= len(correct_answer)*0.8:
                    return False
            return True

    '''
    #TODO: utilize enchant library here and combine with substring checking
    @staticmethod
    def fuzz_answer(given_answer, correct_answer):
        if type(given_answer) != str or type(correct_answer) != str:
            return False
        else:
            # remove casing, whitespace, punctuation, and articles
            given_answer = Host.strip_answer(given_answer)
            correct_answer = Host.strip_answer(correct_answer)
            # count how many mismatched letters we have
            error_count = 0
            error_ratio = len(correct_answer)/8

            #the max acceptable length that we count as close enough
            #for a second chance

            acceptable_length = len(correct_answer)*0.8
            paired_letters = list(zip(given_answer, correct_answer))
            for first_letter, second_letter in paired_letters:
                if first_letter != second_letter:
                    error_count += 1
            # if the answer is too short, don't bother
            if len(given_answer) <= acceptable_length:
                return False
            # check if we got an empty string as an answer
            elif paired_letters and error_count <= error_ratio:
                return True
            else:
                return False
    '''
