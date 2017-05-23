import json
from random import randint

'''
 Class that acts as the "host" of Jeopardy
 e.g. asks clues, gets point values, etc.
'''

'''
Holds details about questions and questions themselves
:str text: The actual text of the question
:str answer: The answer to the question
:int value: The dollar value of the question
:str category: The category of the question
:boolean daily_double: True if question is a daily double
'''

class Question:

    def __init__(self, text, value, category, daily_double, answer):

        self.text = ''
        self.value = 0
        self.category = ''
        self.daily_double = False
        self.answer = ''

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

def get_question():
    jeopardy_json_file = open('./csv_files/JEOPARDY_QUESTIONS1.json').read()
    question = json.loads(jeopardy_json_file)
    # json file has 216,930 questions
    question = question[randint(0, 216930)]
    text = question['question']
    value = question['value']
    category = question['category']
    daily_double = Question.is_daily_double(value)
    answer = question['answer']
    return Question(text, value, category, daily_double, answer)
