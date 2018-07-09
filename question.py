import pdb
import json
import re
from contextlib import suppress
from random import randint
from requests import get as get_http_code
from requests.exceptions import RequestException

# TODO: strip out hyperlinks e.g.

'''
'This patron saint of Lourdes'
<a href="http://www.j-archive.com/media/2004-11-17_DJ_21.jpg"
target="_blank">body</a>
has remained unchanged in its glass display case since her death in 1879'

These might be challenging
<a href="http://www.j-archive.com/media/2010-06-15_DJ_20.jpg" target=
"_blank">What</a> the ant had in song'
'''

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
:str answer: The answer to the question
:int value: The dollar value of the question
:str category: The category of the question
:boolean daily_double: True if question is a daily double
:str asker: User who asked the question
'''
class Question:

    # init
    jeopardy_json_file = open('./support_files/JEOPARDY_QUESTIONS1.json').read()
    question_list = json.loads(jeopardy_json_file)

    def __init__(self):
        question_list = self.question_list
        question_list = self.filter_questions(question_list, banned_categories=\
        'missing this category', banned_phrases=['seen here', 'heard here', 'audio clue'])
        # used to test daily doubles
        # question_list = self.filter_questions(question_list, daily_double=1)
        question = question_list[randint(0, len(question_list))]
        self.text = question['question']
        self.value = Question.convert_value_to_int(question['value'])
        self.category = question['category']
        self.daily_double = Question.is_daily_double(self.value)
        self.answer = question['answer']
        self.date = question['air_date']

    def get_value(self):
        return ('$' + str(self.value))

    '''
    filters list of questions and returns filtered list
    :param question_list: list of questions we pass in (in json form)
    :param daily_double: if this is passed in we filter for only daily doubles
    (for testing purposes)
    :param banned_categories: list of categories to filter out, can be a single
    str category instead
    :param banned_phrases: filters questions by key phrases, such as
    "seen here" or "heard here"
    '''
    def filter_questions(self, question_list, daily_double=None,
    banned_categories=None, banned_phrases=None):
        # if we want to filter for only daily doubles
        if daily_double:
            question_list = list(filter(lambda x: \
            self.is_daily_double(x['value']), question_list))
        # if list of phrases is passed in as arg
        if banned_phrases and type(banned_phrases) is list:
            for phrase in banned_phrases:
                question_list = list(filter(lambda x: phrase.lower() not in \
                x['question'].lower(), question_list))
        # if single phrase is passed in as a string
        elif banned_phrases and type(banned_phrases) is str:
            question_list = list(filter(lambda x: phrase.lower() not in \
            x['question'].lower(), return_list))
        # if list of categories is passed in, these are in upper case in json
        if banned_categories and type(banned_categories) is list:
            banned_categories = [c.upper() for c in banned_categories]
            question_list = list(filter(lambda x: x['category'] not in\
            banned_categories, question_list))
        # if single category is passed in as a string
        elif banned_categories and type(banned_categories) is str:
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
    def separate_html(question):
        with suppress(RequestException):
            # scrub newline chars from question text
            question_text = re.sub(r'\n', '', question)
            # valid links to return
            valid_links = []
            # use regex to check in case link syntax got mangled
            regex_links = re.findall(r'http://.*?\"', question)
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
                return (question_text, valid_links)
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
