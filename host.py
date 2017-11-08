import pdb
import main
import question
import db
from re import sub, compile
from os import path
from contextlib import suppress
from unidecode import unidecode
import difflib
import editdistance

# initialize user database
user_db = db.db('users.db')
# initialize dictionary
eng_dict = ''
if path.isfile('/usr/share/dict/words'):
    words_file = open('/usr/share/dict/words', 'r')
    eng_dict = words_file.readlines()
else:
    eng_dict = open('./support_files/words.txt').read().splitlines()
current_champion_name, current_champion_score = user_db.get_last_nights_champion(user_db.connection)

'''
 Class that acts as the "host" of Jeopardy
 e.g. asks clues, gets point values, etc.
 think of this as the class that handles listening and talking to slack
'''

class Host:

    # what to type before we give trebekbot a command
    command_prefix = '..'
    intro_text = 'This iiiiiis trebekbot! Version: ' + main.build_version
    help_text = '''
    Use '''+command_prefix+''' to prefix commands.
    '''+command_prefix+'''help: bring up this help list
    '''+command_prefix+'''hello: say hello to trebekbot
    '''+command_prefix+'''ask: trebekbot will ask you a question
    '''+command_prefix+'''whatis: use this to provide an answer to the question
    '''+command_prefix+'''myscore: find out what your current score is
    '''+command_prefix+'''topten: find out who the top ten scorers are
    '''+command_prefix+'''wager: put in your wager for daily doubles
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
            channel = self.get_channel(slack_output)
            user = self.get_user(slack_output)
            # prefix without the ';;'
            prefix = text[2:].split(' ')[0]
            # if the text starts with the command_prefix
            # and the rest of the text minus the prefix matches what we're listening for
            # and we're in the right channel
            if text.startswith(self.command_prefix) and channel == main.channel\
            and prefix == listen_for:
                answer = text.split(prefix)[1]
                # add user to db if theyre not in there already
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
        'channels.info',
        channel = channel_id
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
        # in case we don't locate a user
        if user:
            return user['user']['name']

    # COMMANDS

    # lists trebekbot functions
    def help(self, slack_output):
        if self.hear(slack_output, 'help'):
            self.say(main.channel, self.help_text)

    # gets wager value from output for daily doubles
    def get_wager(self, slack_output, user_score):
        with suppress(ValueError):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            wager = int(slack_output['text'].split('wager')[1])
            # jeopardy rules: users below $1000 get up to $1000 to bet
            if user_score < 1000:
                user_score = 1000
            # we don't want to let users bet more than they have
            if wager > user_score:
                return user_score
            # prevent negative bets
            if wager < 0:
                return 0
            else:
                return wager

    # say hi!
    def hello(self, slack_output):
        if self.hear(slack_output, 'hello'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            if current_champion_name and user == current_champion_name:
                user = ':crown:' + user
            self.say(main.channel, 'Hello ' + user)

    # gets a random question from the jeopardy_json_file
    # TODO: make this scrub out html links
    def ask_question(self, slack_output):
        if self.hear(slack_output, 'ask'):
            asked_question = question.Question()
            # parse this so it's pretty in slack
            if asked_question.daily_double:
                question_text = '[*'+asked_question.category+'*] ' + '_'+asked_question.text+'_'
            else:
                question_text = '[*'+asked_question.category+'*] ' + '['+asked_question.get_value()+'] ' + '_'+asked_question.text+'_'
            self.say(main.channel, question_text)
            return asked_question

    '''
    checks if the answer to a question is correct and updates score accordingly
    :param slack_output: the output we hear coming from slack_output
    :param question: the question object
    :param wager: optional, the wager if the question is a Daily Double
    '''
    def check_answer(self, slack_output, question, wager=None):
        # we need this to prevent parsing a blank answer
        if self.hear(slack_output, 'whatis'):
            # init
            # this drills down into the slack output to get the given answer
            slack_output = slack_output[0]
            user_answer = slack_output['text'].split('whatis')[1]
            # who asked the question
            user = self.get_user(slack_output)
            user_id = slack_output['user']
            # what we use to address the user when they answer
            user_address = '<@'+user_id+'|'+user+'>'
            # if the user is the champ, give them a crown!
            if current_champion_name and user == current_champion_name:
                user_address = ':crown: <@'+user_id+'|'+user+'>'
            correct_answer = question.answer
            # check if answer is correct
            answer_check = self.fuzz_answer(user_answer, correct_answer)
            # respond to user
            if answer_check:
                self.say(main.channel, user_address+ ' :white_check_mark: That is correct. The answer is ' +correct_answer)
                # award points to user
                if question.daily_double:
                    user_db.update_score(user_db.connection, user, wager)
                else:
                    user_db.update_score(user_db.connection, user, question.value)
                return 'right'
            elif answer_check is 'close':
                self.say(main.channel, user_address+ ' Please be more specific.')
                return 'close'
            else:
                self.say(main.channel, user_address+ ' :x: Sorry, that is incorrect.')
                # take away points from user
                if question.daily_double and wager:
                    user_db.update_score(user_db.connection, user, -wager)
                else:
                    user_db.update_score(user_db.connection, user, -question.value)


    # returns user's current score
    def myscore(self, slack_output, db):
        if self.hear(slack_output, 'myscore'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            # needed to avoid querying db for name with crown in it
            user_address = user
            if current_champion_name and user == current_champion_name:
                user_address = ':crown: ' + user
            self.say(main.channel, user_address + ', your score is: '+ ' $' + \
            str(db.get_score(db.connection, user)))


    # returns top ten scorers
    def top_ten(self, slack_output):
        if self.hear(slack_output, 'topten'):
            top_ten_list = user_db.return_top_ten(user_db.connection)
            slack_list = 'Here\'s our top scorers: \n'
            count = 1
            # TODO: improve/refactor this
            for champ,name,score,champ_score,id in top_ten_list:
                # give crown for being champ
                if current_champion_name and name == current_champion_name:
                    name = ':crown:' + name
                # format: 1. Morp - $501
                slack_list += str(count) + '. ' + name + ' - ' + '$' \
                + str(score) + '\n'
                count += 1
            self.say(main.channel, slack_list)

    # strips answers of extraneous punctuation, whitespace, etc.
    @staticmethod
    def strip_answer(answer):
        '''
        remove casing, we also prefix a space so the next regex will
        catch articles that start the string (otherwise we'd need a
        '^' in addition to a '\s')
        '''
        answer = ' ' + answer.lower()
        # remove diacritical marks
        answer = unidecode(answer)
        # remove anything in parentheses
        answer = sub(r'\((.*)\)', '', answer)
        '''
        remove articles and conjunctions that are alone or at the start of
        quotations
        '''
        answer = \
        sub(r'\sand\s|\sthe\s|\san\s|\sa\s|\"and\s|\"the\s|\"an\s|\"a|\s', ' ',
        answer)
        # replace hyphens with whitespace
        answer = sub(r'-', ' ', answer)
        # remove anything that's not alphanumeric
        answer = sub(r'[^A-Za-z0-9\s]', '', answer)
        # remove apostrophes
        answer = sub(r'\'', '', answer)
        # clean up extra whitespace (change spaces w/more than one space to
        # a single space)
        answer = sub(r'\s{2,}', ' ', answer)
        # remove leading space and split into array
        return answer[1:].split(' ')

    # checks if given answer is close enough to correct answer
    # TODO: rename this
    @staticmethod
    def fuzz_answer(given_answer, correct_answer):
        if given_answer == 'poker':
            pdb.set_trace()
        # TODO: we may need a dict here so we don't get misaligned zips
        # TODO: make conjunctions/disjunctions behave as logical operators
        # if we get an empty string, don't bother
        if not given_answer:
            return False
        # we only want exact matches if the answer is a number
        try:
            if int(given_answer) != int(correct_answer):
                return False
        except (ValueError):
            # remove casing, punctuation, and articles
            given_answer = Host.strip_answer(given_answer)
            correct_answer = Host.strip_answer(correct_answer)
            zipped_words = list(zip(given_answer, correct_answer))
            for given_word, correct_word in zipped_words:
                # use lambda to pare down dict
                first_letter_eng_dict = filter(lambda x: x[:1] == given_word[:1], eng_dict)
                # get lists of close words (spell check)
                check_given_word_closeness = difflib.get_close_matches \
                (given_word, first_letter_eng_dict, n=5, cutoff=0.8)
                check_correct_word_closeness = difflib.get_close_matches \
                (correct_word, first_letter_eng_dict, n=5, cutoff=0.8)
                # remove newline chars from spell check lists
                check_given_word_closeness = sub(r'\n', ' ', ''.join(check_given_word_closeness)).split(' ')
                check_correct_word_closeness = sub(r'\n', ' ', ''.join(check_correct_word_closeness)).split(' ')
                # get levenshtein distance
                lev_dist = editdistance.eval(given_word, correct_word)

                '''
                if the word is:
                - long enough
                - in the spell check results for both itself and correct word
                - identical to the correct word
                - one levenshtein distance off from correct word
                then keep looping through the words
                elif word is:
                - in the correct word and long enough or in the correct answer
                - or vice versa (but we dont check if correct word is in given answer)
                then it's close enough
                '''

                # TODO: add a substring check where we treat answers as single strings without whitespace
                # via Phebus: check for substring but add word boundaries (e.g. /\s+word\s+/)

                '''
                if given_word in correct_answer and len(given_word) < len(''.join(correct_answer)):
                    return 'close'
                '''

                if len(given_word) >= len(correct_word)*0.8 \
                and given_word in check_given_word_closeness \
                and given_word in check_correct_word_closeness \
                or given_word == correct_word \
                or lev_dist <= 1:
                    continue
                elif given_word in correct_word \
                and len(given_word) >= len(correct_word)*0.8 \
                or correct_word in given_word \
                and len(correct_word) >= len(given_word)*0.8 \
                or given_word in correct_answer:
                    return 'close'
                else:
                    return False
            return True
