from src.question import Question
from os import path, pardir
from random import randint
import json


project_root = path.join(path.dirname(path.abspath(__file__)), pardir)


def create_single_question_fixture() -> dict:
    fixture_json = {}
    pk = 0
    model = 'trebekbot_app.question'
    jeopardy_json_file = open(path.join(project_root, 'support_files', 'JEOPARDY_QUESTIONS1.json')).read()
    question_list = json.loads(jeopardy_json_file)
    q = question_list[randint(0, len(question_list))]
    scrubbed_text = Question.separate_html(q['question'])
    text = ''
    valid_links = []
    if type(scrubbed_text) == str:
        text = scrubbed_text
    # if there are valid html links included in question text
    elif type(scrubbed_text) == list:
        text = scrubbed_text[0]
        valid_links = scrubbed_text[1:]
    value = Question.convert_value_to_int(q['value'])
    new_question_json = {
        'model': model,
        'pk': pk,
        'fields': {
            'text': text,
            'value': value,
            'category': q['category'],
            'daily_double': Question.is_daily_double(value),
            'answer': q['answer'],
            'date': q['air_date'],
            'valid_links': ', '.join(valid_links)
        }
    }
    fixture_json.update(new_question_json)
    return fixture_json


with open('question_fixture_test.json', 'w') as qfix:
    json.dump(create_single_question_fixture(), qfix)
