import json
import re
from random import randint

'''
Holds details about questions and questions themselves
:str text: The actual text of the question
:str answer: The answer to the question
:int value: The dollar value of the question
:str category: The category of the question
:boolean daily_double: True if question is a daily double
:str asker: User who asked the question
'''

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

class Question:

    # init
    jeopardy_json_file = open('./support_files/JEOPARDY_QUESTIONS1.json').read()
    question_list = json.loads(jeopardy_json_file)

    def __init__(self):
        #TODO: remove "heard here/seen here" questions
        # used to test daily doubles
        question_list = self.question_list
        # question_list = self.filter_questions(question_list, daily_double=1)
        # json file has 216,930 questions
        question = question_list[randint(0, 216930)]
        self.text = question['question']
        self.value = Question.convert_value_to_int(question['value'])
        self.category = question['category']
        self.daily_double = Question.is_daily_double(self.value)
        self.answer = question['answer']

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
            return list(filter(lambda x: \
            self.is_daily_double(x['value']), question_list))
        if banned_phrases and type(banned_phrases) is list:
            return_list = question_list
            for phrase in banned_phrases:
                return_list = list(filter(lambda x: phrase not in x['question']\
                , return_list))
            return return_list
        # if list of categories is passed in
        elif banned_categories and type(banned_categories) is list:
            banned_categories = [c.upper() for c in banned_categories]
            return list(filter(lambda x: x['category'] not in\
            banned_categories, question_list))
        # if single category is passed in as a string
        elif banned_categories and type(banned_categories) is str:
            banned_categories = banned_categories.upper()
            return list(filter(lambda x: x['category'] !=\
            banned_categories, question_list))

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

    @staticmethod
    def is_daily_double(value):
        # check if we have a value at all
        if value:
            if type(value) is str:
                value = Question.convert_value_to_int(value)
            if value < 1:
                return False
            elif value > 2000 or value % 100 != 0:
                return True
            else:
                return False
