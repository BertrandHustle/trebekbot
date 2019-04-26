# import pdb
import src.question as question
import src.db as db
from time import time, ctime
from re import sub, findall, match, IGNORECASE
from os import path, environ
from contextlib import suppress
from unidecode import unidecode
from json import decoder
import difflib
import editdistance

# initialize dictionary
eng_dict = ''
if path.isfile('/usr/share/dict/words'):
    words_file = open('/usr/share/dict/words', 'r')
    eng_dict = words_file.readlines()
else:
    eng_dict = open('./support_files/words.txt').read().splitlines()

class Host:
    '''
     Class that acts as the "host" of Jeopardy
     e.g. asks clues, gets point values, etc.
     think of this as the class that handles listening and talking to slack
     :param slack_client: slackclient object
     :param user_db: db object containing connection to user db
    '''

    # what to type before we give trebekbot a command
    command_prefix = '..'
    intro_text = 'This iiiiiis trebekbot!'
    help_text = '''
    Use '''+command_prefix+''' to prefix commands.
    '''+command_prefix+'''help: bring up this help list
    '''+command_prefix+'''hello: say hello to trebekbot
    '''+command_prefix+'''ask: trebekbot will ask you a question
    '''+command_prefix+'''whatis: use this to provide an answer to the question
    '''+command_prefix+'''myscore: find out what your current score is
    '''+command_prefix+'''mywins: find out your all-time win count
    '''+command_prefix+'''topten: find out who the top ten scorers are
    '''+command_prefix+'''wager: put in your wager for daily doubles
    '''+command_prefix+'''pass: pass a daily double if you don't know it
    '''+command_prefix+'''changelog: show latest changelog notes
    '''+command_prefix+'''uptime: show start time of this trebekbot
    '''

    def __init__(self, slack_client, user_db):
        self.uptime = ctime(time())
        self.slack_client = slack_client
        # connect to slack upon init
        slack_client.rtm_connect(auto_reconnect=True)
        # channel id of channel where host currently is
        self.channel_id = self.get_channel_id(environ.get('SLACK_CHANNEL'))
        # connect to user database
        self.user_db = user_db
        # TODO: refactor this, it's duplicated in main.py
        # get current champion info
        self.current_champion_score, self.current_champion_name = None, None
        try:
            self.current_champion_score, self.current_champion_name = \
            self.user_db.get_champion(self.user_db.connection)
        except TypeError:
            pass

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
            channel = slack_output['channel']
            user = self.get_user(slack_output)
            text_minus_prefix = text[2:].split(' ')[0]
            # if the text starts with the command_prefix
            # and the rest of the text minus the prefix matches what we're listening for
            # and we're in the right channel
            if text.startswith(self.command_prefix) \
            and channel == self.channel_id \
            and text_minus_prefix == listen_for:
                answer = text.split(text_minus_prefix)[1]
                # add user to db if theyre not in there already
                self.user_db.add_user_to_db(self.user_db.connection, user)
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
        return channel['channel']['name']

    # mostly here because we can't test the slack api methods
    def get_channel_id_from_json(self, channel_name, channel_json):
        with suppress(IndexError, KeyError, TypeError):
            for channel in channel_json['channels']:
                search_name = channel['name']
                if channel_name == search_name:
                    return channel['id']

    def get_channel_id(self, channel_name):
        channel_list = self.slack_client.api_call(
        'channels.list',
        )
        return self.get_channel_id_from_json(channel_name, channel_list)

    '''
    get bot's slack id
    :param bot_name:
    '''
    def get_bot_id(self, bot_name):
        api_call = self.slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('name') == bot_name:
                    return user.get('id')

    '''
    get user by checking user id
    :param slack_output: json of user message from slack
    '''
    def get_user(self, slack_output):
        with suppress(decoder.JSONDecodeError):
            user_id = slack_output['user']
            user = self.slack_client.api_call(
            'users.info',
            user = user_id
            )
            # in case we don't locate a user
            if user:
                return user['user']['name']

    # returns bugfix/feature notes for latest version of trebekbot
    def get_latest_changelog(self, changelog_path):
        # the text from the latest changelog only, this is what we will return
        latest_changelog = ''
        '''
        flag that trips when the latest changelog has been found,
        because we'll be returning a paragraph this stays tripped until we hit
        a blank line
        '''
        found_latest = False
        with open(changelog_path, 'r', encoding='utf8') as changelog:
            for line in changelog.readlines():
                version_number_line = match(r'version\s\d.\d.\d', line, IGNORECASE)
                if version_number_line and not found_latest:
                    found_latest = True
                    latest_changelog += line
                elif version_number_line and found_latest :
                    return latest_changelog
                elif found_latest:
                    latest_changelog += line

    '''
    gets wager value from output for daily doubles
    :param: slack_output: json of user message from slack
    :param: user_score: the current score of the user making the wager
    '''
    def get_wager(self, slack_output, user_score):
        with suppress(ValueError):
            slack_output = slack_output[0]
            wager = int(slack_output['text'].split('wager')[1])
            return self.calc_wager(wager, user_score)

    '''
    adjusts wager according to jeopardy rules, this is separate from get_wager
    to bypass slack api for unit testing
    '''
    @staticmethod
    def calc_wager(wager, user_score):
        # we want this to return a None if we get a TypeError, that way
        # trebekbot will re-prompt for a wager
        with suppress(TypeError):
            # jeopardy rules: users below $1000 get up to $1000 to bet
            if user_score < 1000:
                user_score = 1000
            # we don't want to let users bet more than they have
            if wager > user_score:
                return user_score
            # a 0 wager is not a wager
            if not wager:
                return None
            # prevent negative bets
            if wager < 0:
                return 0
            else:
                return wager

    # COMMANDS

    # lists trebekbot functions
    def help(self, slack_output):
        if self.hear(slack_output, 'help'):
            self.say(self.channel_id, self.help_text)

    # shows latest changelog
    def changelog(self, slack_output):
        if self.hear(slack_output, 'changelog'):
            self.say(self.channel_id, self.get_latest_changelog('README.md'))

    # shows time trebekbot was last booted up (uptime)
    def say_uptime(self, slack_output):
        if self.hear(slack_output, 'uptime'):
            self.say(self.channel_id, self.uptime)

    # say hi!
    def hello(self, slack_output):
        if self.hear(slack_output, 'hello'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            if self.current_champion_name and user == self.current_champion_name:
                user = ':crown:' + user
            self.say(self.channel_id, 'Hello ' + user)

    # returns user's current score
    def myscore(self, slack_output, db):
        if self.hear(slack_output, 'myscore'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            # needed to avoid querying db for name with crown in it
            user_address = user
            if self.current_champion_name and user == self.current_champion_name:
                user_address = ':crown: ' + user
            self.say(self.channel_id, user_address + ', your score is: '+ ' $' + \
            str(db.get_score(db.connection, user)))

    # returns top ten scorers
    # if force flag is active, ignore slack and say the top ten regardless (for testing)
    def top_ten(self, slack_output, force=None):
        if self.hear(slack_output, 'topten') or force:
            top_ten_list = self.user_db.return_top_ten(self.user_db.connection)
            slack_list = 'Here\'s our top scorers: \n'
            count = 1
            # TODO: improve/refactor this
            for champ,name,score,champ_score,id, wins in top_ten_list:
                # give crown for being champ
                if self.current_champion_name and name == self.current_champion_name:
                    name = ':crown: ' + name
                # format: 1. Morp - $501
                slack_list += str(count) + '. ' + name + ' - ' + '$' \
                + str(score) + '\n'
                count += 1
            self.say(self.channel_id, slack_list)

    # TODO: finish writing this
    # gets total all-time wins for user
    def mywins(self, slack_output):
        if self.hear(slack_output, 'mywins'):
            slack_output = slack_output[0]
            user = self.get_user(slack_output)
            if self.current_champion_name and user == self.current_champion_name:
                user = ':crown: ' + user
            wins = str(self.user_db.get_user_wins(self.user_db.connection, user))
            self.say(self.channel_id, user + ' wins: ' + wins)


    '''
    gets a random question from the jeopardy_json_file
    :param slack_output: the output we hear coming from slack_output
    :param test_question: allows us to feed in a question for testing rather
    than getting a random one from the json
    '''
    def ask_question(self, slack_output):
        if self.hear(slack_output, 'ask'):
            asked_question = question.Question()
            self.say(self.channel_id, asked_question.slack_text)
            return asked_question

    # DEBUG_COMMANDS

    # crashes trebekbot to force a restart
    def crash(self, slack_output):
        if self.hear(slack_output, 'crash'):
            slack_output = slack_output[0]
            if self.get_user(slack_output) == 'bertrand_hustle':
                raise Exception

    # asks daily double, but only if it's bertrand_hustle
    def debug_daily_double(self, slack_output):
        if self.hear(slack_output, 'dd'):
            slack_output = slack_output[0]
            # this can't be an 'and' because we need valid slack output first
            if self.get_user(slack_output) == 'bertrand_hustle':
                asked_question = question.Question(daily_double_debug=True)
                self.say(self.channel_id, asked_question.slack_text)
                return asked_question

    '''
    check if user needs to be more specific or less specific in their answer
    :string user_answer: answer given by user
    :string correct_answer: correct answer to question
    '''
    def check_closeness(self, user_answer, correct_answer):
        # this will be either 'more' or 'less' depending on closeness to answer
        closeness = None
        # if user answer has equal or less words than correct answer
        if len(user_answer.split(' ')) <= len(correct_answer.split(' ')):
            closeness = 'more'
        # if user answer has more words than correct answer
        else:
            closeness = 'less'
        return 'Please be {} specific.'.format(closeness)

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
            if self.current_champion_name and user == self.current_champion_name:
                user_address = ':crown: <@'+user_id+'|'+user+'>'
            correct_answer = question.answer
            # TODO: refactor this so it can be unit tested
            # check if answer is correct
            answer_check = self.fuzz_answer(user_answer, correct_answer)
            # respond to user
            if answer_check is 'close':
                self.say(
                self.channel_id,
                user_address + ' ' + \
                self.check_closeness(user_answer, correct_answer)
                )
                return 'close'
            # right answer
            elif answer_check is True:
                self.say(self.channel_id, user_address+ ' :white_check_mark: That is correct. The answer is ' +correct_answer)
                # award points to user
                if question.daily_double:
                    self.user_db.update_score(self.user_db.connection, user, wager)
                else:
                    self.user_db.update_score(self.user_db.connection, user, question.value)
                return 'right'
            # wrong answer
            elif answer_check is False:
                self.say(self.channel_id, user_address+ ' :x: Sorry, that is incorrect.')
                # take away points from user
                if question.daily_double and wager:
                    self.user_db.update_score(self.user_db.connection, user, -wager)
                else:
                    self.user_db.update_score(self.user_db.connection, user, -question.value)

    # strips answers of extraneous punctuation, whitespace, etc.
    @staticmethod
    def strip_answer(answer):
        # ok, not technically ALL articles
        articles = ['and', 'the', 'an', 'a', 'of']
        '''
        remove casing, we also prefix a space so the next regex will
        catch articles that start the string (otherwise we'd need a
        '^' in addition to a '\s')
        '''
        answer = ' ' + answer.lower()
        # remove diacritical marks
        answer = unidecode(answer)
        # remove anything in parentheses
        # https://stackoverflow.com/questions/17779744/regular-expression-to-get-a-string-between-parentheses-in-javascript
        answer = sub(r'\(([^)]+)\)', '', answer)
        '''
        remove articles and conjunctions that are alone, at the start of
        quotations, or at the beginning of the string
        '''
        for a in articles:
            answer = sub(r'\s{}\s|\"{}\s|^{}\s'.format(a, a, a), ' ', answer)
        # exception for "spelling bee" answers e.g. S-P-E-L-L
        # if ' s-p-e-l-l' in answer:
             #pdb.set_trace()
        if not match(r'\s|\w-\w-.+', answer):
            # replace hyphens with whitespace
            answer = sub(r'-', ' ', answer)
        else:
            answer = sub(r'-', '', answer)
        # remove anything that's not alphanumeric
        answer = sub(r'[^A-Za-z0-9\s]', '', answer)
        # remove apostrophes
        answer = sub(r'\'', '', answer)
        # clean up extra whitespace (change spaces w/more than one space to
        # a single space, and removes leading and trailing spaces)
        answer = sub(r'\s{2,}', ' ', answer)
        answer = sub(r'^\s*|\s*$', '', answer)
        return answer.split(' ')

    # makes list of word-pairs out of given/correct answer arrays (arrays of words)
    # these arrays will always be filtered through strip_answer() first
    @staticmethod
    def pair_off_answers(answer1, answer2):
        matrix = []
        for word in answer1:
            for comp_word in answer2:
                # convert to set so order doesn't matter in pairs
                if not set([word, comp_word]) in [set(m) for m in matrix]:
                    matrix.append((word, comp_word))
        return matrix

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

    @staticmethod
    def fuzz_word(given_word, correct_word):
        given_word, correct_word = given_word.lower(), correct_word.lower()
        if given_word == correct_word:
            return True
        else:
            # use lambda to pare down comparison dictionary
            first_letter_eng_dict = list(filter(lambda x: x[:1] == given_word[:1], eng_dict))

            # get lists of close words (spell check)
            check_given_word_closeness = difflib.get_close_matches \
            (given_word, first_letter_eng_dict, n=5, cutoff=0.8)

            check_correct_word_closeness = difflib.get_close_matches \
            (correct_word, first_letter_eng_dict, n=5, cutoff=0.8)

            # remove newline chars from spell check lists
            check_given_word_closeness = sub(r'\n', ' ', ' '.join(check_given_word_closeness)).split(' ')
            check_correct_word_closeness = sub(r'\n', ' ', ' '.join(check_correct_word_closeness)).split(' ')

            # get levenshtein distance
            lev_dist = editdistance.eval(given_word, correct_word)
            # check to see if word is in spell check list for both words
            is_in_both_dicts = given_word in check_given_word_closeness \
            and given_word in check_correct_word_closeness
            # check for proper nouns (in other words: is the word
            # in a standard dictionary?)
            not_in_dict = not given_word in check_given_word_closeness \
            and not given_word in check_correct_word_closeness
            # difference between the lengths of the two words
            length_diff = abs(len(given_word) - len(correct_word))
            # is the length of the guessed word close enough to the correct word?
            is_long_enough = length_diff <= \
            max(len(given_word), len(correct_word)) * 0.3

            if is_long_enough and is_in_both_dicts or lev_dist <= 1:
                return True
            elif is_in_both_dicts and \
            (given_word in correct_word or correct_word in given_word) \
            and lev_dist <= 2:
                return 'close'
            elif not_in_dict and lev_dist <=2 and len(given_word) == len(correct_word):
                return 'close'
            else:
                return False

    # checks if given answer is close enough to correct answer
    # TODO: rename this
    # TODO: make conjunctions/disjunctions behave as logical operators

    @staticmethod
    def fuzz_answer(given_answer, correct_answer):
        # we need a copy of the answer with the parenthesized words left in if the correct answer contains parentheses
        paren_answer = None
        paren_close = 0
        paren_right = 0
        # if we get an empty string, don't bother
        if not given_answer:
            return False
        # exception for single letter answers
        if len(given_answer) == 1 and len(correct_answer) == 1:
            return given_answer == correct_answer
        # TODO: make this handle ampersands, etc.
        # account for slashes
        '''
        if '/' in correct_answer:
            correct_answer = correct_answer.split('/')
        correct_answer = list(correct_answer)
        for answer in correct_answer:
        '''
        # we only want exact matches if the answer is a number
        try:
            # prevents cases like '0' or '00'
            if given_answer.startswith('0'):
                raise ValueError
            elif int(given_answer) != int(correct_answer):
                return False
            elif int(given_answer) == int(correct_answer):
                return True
        except (ValueError):
            # flag if the answer contains parentheses
            parentheses = '(' and ')' in correct_answer
            # total up how many word pair comparisons are right, wrong, etc.
            # that is: is the word close enough to the word we're comparing it to?
            right = 0
            close = 0
            '''
            this gives us two copies of the right answer: one with parentheses and one without
            we check both and use the copy with the higher score
            '''
            if parentheses:
                paren_answer = ''.join(list(filter(lambda x: x not in ['(', ')'], correct_answer)))
                paren_answer = Host.strip_answer(paren_answer)
                paren_pair_list = Host.pair_off_answers(Host.strip_answer(given_answer), paren_answer)
                for pair in paren_pair_list:
                    # check equality first for performance boost
                    result = pair[0] == pair[1] or Host.fuzz_word(pair[0], pair[1])
                    if result == 'close':
                        paren_close += 1
                    elif result == True:
                        paren_right += 1
            # remove casing, punctuation, and articles
            given_answer = Host.strip_answer(given_answer)
            correct_answer = Host.strip_answer(correct_answer)
            pair_list = Host.pair_off_answers(given_answer, correct_answer)
            # if 'wells' in given_answer:
                # pdb.set_trace()
            if given_answer == correct_answer or given_answer == paren_answer:
                return True
            # compare pairs and adjust totals accordingly
            for pair in pair_list:
                # check equality first for performance boost
                result = pair[0] == pair[1] or Host.fuzz_word(pair[0], pair[1])
                if result == 'close':
                    close += 1
                elif result == True:
                    right += 1
            # use whichever answer copy has the higher score
            if parentheses:
                close = max(paren_close, close)
                right = max(paren_right, right)
            # check if the answer is close enough
            if right >= round(0.75 * max(len(correct_answer), len(given_answer))):
                return True
            # prevents rounding down to 0
            elif right + close >= max(round(0.5 * max(len(correct_answer), len(given_answer))), 1):
                return 'close'
            else:
                return False
