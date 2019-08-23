import pdb
import json
import re
from os import path, pardir
from contextlib import suppress
from random import randint
from requests import get as get_http_code
from requests.exceptions import RequestException

project_root = path.join(path.dirname(path.abspath(__file__)), pardir)

'''
json example:
{"category": "HISTORY",
"air_date": "2004-12-31",
"question": "'For the last 8 years of his life,
Galileo was under house arrest for espousing this man's theory'",
"value": "$200",
"answer": "Copernicus"
"round": "Jeopardy!"
"show_number": 4680}
'''

'''
Holds details about questions and questions themselves
:str text: The actual text of the question
:int value: The dollar value of the question
:str category: The category of the question
:boolean daily_double: True if question is a daily double
:str answer: The answer to the question
:str date: Date the question was originally aired
:str slack_text: The formatted text we push to slack when question is requested
:list links: List of valid image/audio links associated with question
'''
class Question:

    # init
    banned_categories = 'missing this category',
    banned_phrases = ['seen here', 'heard here', 'audio clue']

    def __init__(self, timer):
        question = self.get_random_question()
        # text with html links separated out
        scrubbed_text = Question.separate_html(question['question'])
        self.text = ''
        self.valid_links = []
        if type(scrubbed_text) == str:
            self.text = scrubbed_text
        # if there are valid html links included in question text
        elif type(scrubbed_text) == list:
            self.text = scrubbed_text[0]
            self.valid_links = scrubbed_text[1:]
        self.value = Question.convert_value_to_int(question['value'])
        self.category = question['category']
        self.daily_double = Question.is_daily_double(self.value)
        self.answer = question['answer']
        self.date = question['air_date']
        self.slack_text = Question.format_slack_text(self)
        self.timer = timer

    # gets random question from given json file
    @staticmethod
    def get_random_question(daily_double=None):
        jeopardy_json_file = open(path.join(project_root, 'support_files', 'JEOPARDY_QUESTIONS1.json')).read()
        question_list = json.loads(jeopardy_json_file)
        # pdb.set_trace()
        question_list = Question.filter_questions(
        question_list,
        daily_double=daily_double,
        banned_categories=Question.banned_categories,
        banned_phrases=Question.banned_phrases
        )
        question = question_list[randint(0, len(question_list))]
        return question

    # formats text to be pretty for slack
    @staticmethod
    def format_slack_text(question):
        if question.daily_double:
            question_text = '[*'+question.category+'*] ' + \
            '['+question.date+'] ' + \
            '_'+question.text+'_'
        else:
            question_text = '[*'+question.category+'*] ' + \
            '['+question.get_value()+'] ' + \
            '['+question.date+'] ' + \
            '_'+question.text+'_'
        if question.valid_links:
            for link in question.valid_links:
                question_text += '\n'+link
        return question_text

    def get_value(self):
        return ('$' + str(self.value))

    '''
    filters list of questions and returns filtered list
    :param question_list: list of questions we pass in (in json form)
    :param banned_categories: list of categories to filter out, can be a single
    str category instead
    :param banned_phrases: filters questions by key phrases, such as
    "seen here" or "heard here"
    '''
    @staticmethod
    def filter_questions(question_list,
    banned_categories=None, banned_phrases=None):
        # if list of phrases is passed in as arg
        if banned_phrases and type(banned_phrases) is list:
            for phrase in banned_phrases:
                question_list = list(filter(lambda x: phrase.lower() not in \
                x['question'].lower(), question_list))
        # if single phrase is passed in as a string
        elif banned_phrases and type(banned_phrases) is str:
            question_list = list(filter(lambda x: phrase.lower() not in \
            x['question'].lower(), question_list))
        # if list of categories is passed in, these are in upper case in json
        if banned_categories and type(banned_categories) is list:
            # 'missing this category' is the only non-capitalized category
            banned_categories = [c.upper() for c in banned_categories \
            if c != 'missing this category']
            question_list = list(filter(lambda x: x['category'] not in\
            banned_categories, question_list))
        # if single category is passed in as a string
        elif banned_categories and type(banned_categories) is str:
            if banned_categories != 'missing this category':
                banned_categories = banned_categories.upper()
            question_list = list(filter(lambda x: x['category'] !=\
            banned_categories, question_list))
        return question_list

    # to remove $ and commas from question values, e.g. '$2,500'
    @staticmethod
    def convert_value_to_int(value):
        try:
            # remove special characters if this is a string
            if type(value) == str:
                # check for negative numbers that haven't been converted to int yet
                if '-' in value:
                    return 0
                else:
                    # remove whitespace/symbols and convert to int
                    value = ''.join(c for c in value if c.isalnum())
                    value = int(value)
            # check to make sure value is over $1
            if value < 1:
                return 0
            else:
                return value
        except (ValueError, TypeError) as error:
            return 0

    '''
    separates html links from questions
    returns a tuple of the question text and link if link is valid,
    otherwise just returns the text
    '''
    @staticmethod
    def separate_html(question_text):
        with suppress(RequestException):
            # scrub newline chars from question text
            question_text = re.sub(r'\n', '', question_text)
            # valid links to return
            valid_links = []
            # use regex to check in case link syntax got mangled
            regex_links = re.findall(r'http://.*?\"', question_text)
            # remove trailing quotes
            regex_links = [link[:-1] for link in regex_links]
            # scrub out html from question
            question_text = re.sub(r'<.*?>', '', question_text)
            if regex_links:
                for link in regex_links:
                    # slice up the link to remove extra quotes
                    if get_http_code(link).status_code in [200, 301, 302]:
                        valid_links.append(link)
            # clean up extra whitespace (change spaces w/more than one space to
            # a single space)
            question_text = re.sub(r'\s{2,}', ' ', question_text)
            # remove leading and trailing spaces
            question_text = question_text.strip()
            # only return links if they're valid, otherwise we just want the
            # scrubbed text
            if valid_links:
                return [question_text] + valid_links
            else:
                return question_text

    @staticmethod
    def is_daily_double(value):
        # we need this edge case in case the value passed in is 0
        if value is 0:
            return True
        # check if we have a value at all
        if value:
            if type(value) is str:
                value = Question.convert_value_to_int(value)
            if value < 1:
                return True
            elif value > 2000 or value % 100 != 0:
                return True
            else:
                return False
