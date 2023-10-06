import datetime
import json

from django.core.management.base import BaseCommand, CommandError

from game.models import Question

# TODO: fix this error
"""
88408
(<Question: A STATE OF CIVIL WAR | 800 | 2005-10-24 | 'On September 17, 1862 Gen. Robert E. Lee's Northern march was halted in this slave-holding Union state'>, False) saved
88409
(<Question: THE "I"s HAVE IT | 800 | 2005-10-24 | 'Christopher Buckley quipped that the name of these theatres stands for "I make the audience cross-eyed"'>, False) saved
CommandError: cannot unpack non-iterable NoneType object
"""


class Command(BaseCommand):
    help = 'populate db with questions from jeopardy json'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_path', type=str, help='path to jeopardy json', default='support_files/JEOPARDY_QUESTIONS1.json'
        )

    @staticmethod
    def filter_questions(question_list, banned_categories=None, banned_phrases=None, category=None) -> list:
        """
        filters list of questions and returns filtered list
        :param question_list: list of questions we pass in (in json form)
        :param banned_categories: list of categories to filter out, can be a single
        str category instead
        :param banned_phrases: filters questions by key phrases, such as
        "seen here" or "heard here"
        :param category: filters list to questions from the given category
        :return list
        """
        if category:
            question_list = list(filter(lambda x: category.lower() == x['category'].lower(), question_list))
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
            question_list = list(filter(lambda x: x['category'] not in \
                                                  banned_categories, question_list))
        # if single category is passed in as a string
        elif banned_categories and type(banned_categories) is str:
            if banned_categories != 'missing this category':
                banned_categories = banned_categories.upper()
            question_list = list(filter(lambda x: x['category'] != \
                                                  banned_categories, question_list))
        return question_list

    def handle(self, *args, **options):
        jeopardy_json_file = open(options['json_path']).read()
        filtered_question_list = self.filter_questions(
            json.loads(jeopardy_json_file),
            banned_categories=Question.banned_categories,
            banned_phrases=Question.banned_phrases,
        )
        question_counter = 0
        try:
            for question_json in filtered_question_list:
                text, valid_links = Question.separate_html(question_json['question'])
                value = Question.convert_value_to_int(question_json['value'])
                new_question = Question.objects.get_or_create(
                    text=text,
                    value=value,
                    category=question_json['category'],
                    daily_double=Question.is_daily_double(value),
                    answer=question_json['answer'],
                    valid_links=valid_links,
                    air_date=datetime.datetime.strptime(question_json['air_date'], '%Y-%m-%d').date()
                )
                question_counter += 1
                print(question_counter)
                print(f'{new_question} saved')
        except Exception as e:
            raise CommandError(e)
