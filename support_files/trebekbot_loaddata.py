from src.question import Question
from os import path, pardir
import json


project_root = path.join(path.dirname(path.abspath(__file__)), pardir)


def create_question_fixture() -> dict:
    """
    grabs questions from provided json and converts them into django-friendly json (fixture)
    :return dict: fixture json
    """
    fixture_json = []
    pk = 1
    model = 'game.question'
    for q in json.loads(open(path.join(project_root, 'support_files', 'JEOPARDY_QUESTIONS1.json')).read()):
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
        pk += 1
        fixture_json.append(new_question_json)
    return fixture_json


with open('../game/fixtures/question_fixture.json', 'w') as qfix:
    json.dump(create_question_fixture(), qfix)

print('COMPLETE!')