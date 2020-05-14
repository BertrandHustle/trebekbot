# native
from time import time, ctime
from re import match, IGNORECASE
from os import environ
from contextlib import suppress
# project
from src.judge import Judge
# thirdparty
from slack import WebClient


class Host:
    """
     Class that acts as the "host" of Jeopardy
     e.g. asks clues, gets point values, etc.
     think of this as the class that handles listening and talking to slack
     :param slack_client: slackclient object
     :param user_db: db object containing connection to user db
    """

    # what to type before we give trebekbot a command
    command_prefix = '/'
    intro_text = 'This iiiiiis trebekbot!'
    help_text = '''
    Use '''+command_prefix+''' to prefix commands.
    '''+command_prefix+'''help: bring up this help list
    '''+command_prefix+'''hello: say hello to trebekbot
    '''+command_prefix+'''ask: trebekbot will ask you a question
    '''+command_prefix+'''next: get a new question from the previous category
    '''+command_prefix+'''skip: skip current question
    '''+command_prefix+'''whatis: use this to provide an answer to the question
    '''+command_prefix+'''myscore: find out what your current score is
    '''+command_prefix+'''mywins: find out your all-time win count
    '''+command_prefix+'''topten: find out who the top ten scorers are
    '''+command_prefix+'''wager: put in your wager for daily doubles
    '''+command_prefix+'''nope: pass a daily double if you don't know it
    '''+command_prefix+'''changelog: show latest changelog notes
    '''+command_prefix+'''uptime: show start time of this trebekbot
    '''

    def __init__(self, slack_token, user_db):
        self.uptime = ctime(time())
        self.slack_client = WebClient(token=slack_token)
        # channel where trebekbot lives
        self.channel = environ.get('SLACK_CHANNEL')
        # connect to user database
        self.user_db = user_db
        # get current champion info
        self.current_champion_name, self.current_champion_score = None, None
        try:
            self.current_champion_name, self.current_champion_score = \
            self.user_db.get_champion(self.user_db.connection)
        except TypeError:
            pass
        # create leaderboard
        self.init_leaderboard()
        # host introduces itself to channel
        self.say(self.channel, self.intro_text)
        self.say(self.channel, self.help_text)
        # announce champ
        if self.current_champion_name and self.current_champion_score > 0:
            # add a win to the user's all-time win count
            user_db.increment_win(user_db.connection, self.current_champion_name)
            self.say(self.channel, 'Let\'s welcome back last night\'s returning champion, \
            :crown: @' + self.current_champion_name + '!')
            self.say(self.channel, 'With a total cash winnings of '+ \
            '$' + str(self.current_champion_score) + '!')
        # show yesterday's leaderboard
        self.say(self.channel, 'Here\'s yesterday\'s top scores:')
        self.say(self.channel, self.top_ten())
        # reset champion_scores here
        user_db.wipe_scores(user_db.connection)

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

    # create leaderboard of users
    def init_leaderboard(self, **payload):
        # get list of users in channel
        for user in self.slack_client.users_list()['members']:
            username = user['name']
            # trebekbot isn't playing!
            if 'trebekbot' not in username:
                self.user_db.add_user_to_db(self.user_db.connection, name)

    # say things back to channel
    def say(self, channel, message, **payload):
        """
        :param: channel: channel to which we are posting message
        :param: message: message to post or 'say'
        """
        self.slack_client.chat_postMessage(
            channel=channel,
            text=message,
            as_user=True
        )

    def create_user_address(self, user_name, user_id):
        """
        creates string to address user and adds crown if user is current champ
        :param: user_name
        :param: user_id
        """
        if self.current_champion_name == user_name:
            return ':crown: <@'+user_id+'>'
        else:
            return '<@'+user_id+'>'

    def create_daily_double_address(self, user_name, user_id):
        """
        creates string to address user if a daily double is asked
        :param: user_name
        :param: user_id
        """
        user_address = self.create_user_address(user_name, user_id)
        user_score = self.my_score(user_name, user_id)
        return 'It\'s a DAILY DOUBLE!\n' + user_address + \
        ' [$' + user_score + '] ' + \
        'Please enter a wager with the /wager command'

    def get_bot_id(self, bot_name):
        """
        get bot's slack id
        :param bot_name:
        """
        api_call = self.slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('name') == bot_name:
                    return user.get('id')

    # returns bugfix/feature notes for latest version of trebekbot
    def get_latest_changelog(self, changelog_path):
        # the text from the latest changelog only, this is what we will return
        latest_changelog = ''
        """
        flag that trips when the latest changelog has been found,
        because we'll be returning a paragraph this stays tripped until we hit
        a blank line
        """
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
    :param: wager: user's raw wager (before we check against user score)
    :param: user_name:
    :param: user_id:
    '''
    def get_wager(self, wager, user_name, user_id):
        user_score = self.user_db.get_score(self.user_db.connection, user_name)
        user_address = self.create_user_address(user_name, user_id)
        user_wager = self.calc_wager(wager, user_score)
        # TODO: fix this!
        # broken values: 1000 None 0
        print(wager, user_wager, user_score)
        if user_wager:
            return user_address + ' you\'ve wagered $' + str(user_wager)
        else:
            return user_address + ' please enter a real wager!'

    '''
    adjusts wager according to jeopardy rules, this is separate from get_wager
    to bypass slack api for unit testing
    '''
    @staticmethod
    def calc_wager(wager, user_score: int):
        # we want this to return a None if we get a TypeError, that way
        # trebekbot will re-prompt for a wager
        with suppress(TypeError, ValueError):
            wager = int(wager)
            # jeopardy rules: users below $1000 get up to $1000 to bet
            if user_score < 1000:
                user_score = 1000
            # we don't want to let users bet more than they have
            if wager > user_score:
                return user_score
            # a 0 or below wager is not a valid wager
            if not wager or wager < 0:
                return None
            else:
                return wager

    def check_answer(self, question, user_answer, user_name, user_id, wager=None):
        '''
        checks if the answer to a question is correct and updates score accordingly
        :param slack_output: the output we hear coming from slack_output
        :param question: the question object
        :param user_answer: the answer given by user
        :param user_name: name of user answering question
        :param user_id: id of user answering question
        :param wager: optional, the wager if the question is a Daily Double
        '''
        user_address = self.create_user_address(user_name, user_id)
        correct_answer = question.answer
        # check if answer is correct
        answer_check = Judge.fuzz_answer(user_answer, correct_answer)
        # if answer is close but not wrong
        if answer_check == 'close':
            return user_address + ' ' + \
            Judge.check_closeness(user_answer, correct_answer)
        # right answer
        elif answer_check == True:
            # award points to user
            if question.daily_double:
                self.user_db.update_score(
                self.user_db.connection, user_name, wager
                )
            else:
                self.user_db.update_score(
                self.user_db.connection, user_name, question.value
                )
            return user_address + \
            ' :white_check_mark: That is correct. The answer is ' \
            +correct_answer
        # wrong answer
        elif answer_check == False:
            # take away points from user
            if question.daily_double and wager:
                self.user_db.update_score(
                self.user_db.connection, user_name, -wager
                )
            else:
                self.user_db.update_score(
                self.user_db.connection, user_name, -question.value
                )
            return user_address + ' :x: Sorry, that is incorrect.'

    # COMMANDS

    '''
    gets user's current score
    :param: user_name:
    :param: user_id:
    '''
    def my_score(self, user_name, user_id):
        user_score = str(
            self.user_db.get_score(self.user_db.connection, user_name)
        )
        user_address = self.create_user_address(user_name, user_id)
        return user_address + ' your score is: ' + ' $' + user_score

    # returns top ten scorers
    def top_ten(self):
        top_ten_list = self.user_db.return_top_ten(self.user_db.connection)
        slack_list = 'Here\'s our top scorers: \n'
        count = 1
        # TODO: improve/refactor this
        for id, name, score, wins in top_ten_list:
            # give crown for being champ
            if self.current_champion_name and name == self.current_champion_name:
                name = ':crown: ' + name
            # format: 1. Morp - $501
            slack_list += '{count}. {name} - ${score}\n'.format(
                count=str(count), name=name, score=str(score)
            )
            '''
            slack_list += str(count) + '. ' + name + ' - ' + '$' \
            + str(score) + '\n'.format
            '''
            count += 1
        return slack_list

    # gets total all-time wins for user
    def my_wins(self, user_name, user_id):
        user_address = self.create_user_address(user_name, user_id)
        wins = str(
        self.user_db.get_user_wins(self.user_db.connection, user_name)
        )
        return user_address + ' wins: ' + wins