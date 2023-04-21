import datetime
import json
import re
from os import path, pardir
from contextlib import suppress
from random import randint

from requests import get as get_http_code
from requests.exceptions import RequestException

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

project_root = path.join(path.dirname(path.abspath(__file__)), pardir)

ROOM_LIMIT = 3

# Validators


# def room_is_full(players):
#     if len(players) > ROOM_LIMIT:
#         raise ValidationError('Room limit reached!')

# Models


class Player(AbstractUser):
    score = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)

    def __str__(self):
        return self.username

    # @receiver(post_save, sender=User)
    # def create_user_profile(self, sender, instance, created, **kwargs):
    #     if created:
    #         self.objects.create(user=instance)
    #
    # @receiver(post_save, sender=User)
    # def save_user_profile(self, sender, instance, **kwargs):
    #     instance.profile.save()


class Question(models.Model):

    """
    Holds details about questions and questions themselves
    :str text: The actual text of the question
    :int value: The dollar value of the question
    :str category: The category of the question
    :boolean daily_double: True if question is a daily double
    :str answer: The answer to the question
    :str date: Date the question was originally aired
    :str slack_text: The formatted text we push to slack when question is requested
    :list links: List of valid image/audio links associated with question
    """

    """
    json example:
    {"category": "HISTORY",
    "air_date": "2004-12-31",
    "question": "'For the last 8 years of his life,
    Galileo was under house arrest for espousing this man's theory'",
    "value": "$200",
    "answer": "Copernicus"
    "round": "Jeopardy!"
    "show_number": 4680}
    """

    text = models.CharField(max_length=750)
    value = models.IntegerField()
    category = models.CharField(max_length=100)
    daily_double = models.BooleanField(default=False)
    answer = models.CharField(max_length=250)
    valid_links = models.CharField(max_length=500, blank=True, default='')
    air_date = models.DateField()

    def __str__(self):
        return f'{self.category} | {self.value} | {self.date} | {self.text}'

    banned_categories = 'missing this category'
    banned_phrases = ['seen here', 'heard here', 'audio clue']

    # gets random question from given json file
    @staticmethod
    def get_random_question(category=None):
        jeopardy_json_file = open(path.join(project_root, 'support_files', 'JEOPARDY_QUESTIONS1.json')).read()
        # TODO: load this into memory once, not every time
        question_list = Question.filter_questions(
            json.loads(jeopardy_json_file),
            banned_categories=Question.banned_categories,
            banned_phrases=Question.banned_phrases,
            category=category
        )
        question_id = randint(0, len(question_list))
        question_json = question_list[question_id]
        return Question(question_json), question_id

    def get_value(self):
        return '$' + str(self.value)

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
                question_list = list(filter(lambda x: phrase.lower() not in x['question'].lower(), question_list))
        # if single phrase is passed in as a string
        elif banned_phrases and type(banned_phrases) is str:
            question_list = list(filter(lambda x: phrase.lower() not in x['question'].lower(), question_list))
        # if list of categories is passed in, these are in upper case in json
        if banned_categories and type(banned_categories) is list:
            # 'missing this category' is the only non-capitalized category
            banned_categories = [c.upper() for c in banned_categories if c != 'missing this category']
            question_list = list(filter(lambda x: x['category'] not in banned_categories, question_list))
        # if single category is passed in as a string
        elif banned_categories and type(banned_categories) is str:
            if banned_categories != 'missing this category':
                banned_categories = banned_categories.upper()
            question_list = list(filter(lambda x: x['category'] != banned_categories, question_list))
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
            return question_text, valid_links

    @staticmethod
    def is_daily_double(value):
        # we need this edge case in case the value passed in is 0
        if value == 0:
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

    @staticmethod
    def get_questions_by_category(category: str, timer) -> list:
        """returns all questions for a given category
        :param category
        :param timer: timer object used to construct Question
        :return: list of questions
        """
        search_category = category.upper()
        jeopardy_json_file = open(path.join(project_root, 'support_files', 'JEOPARDY_QUESTIONS1.json')).read()
        question_list = json.loads(jeopardy_json_file)
        categorized_question_jsons = list(filter(lambda x: search_category == x['category'], question_list))
        return [Question(q, timer) for q in categorized_question_jsons]

    def save_all_questions_to_db(self):
        jeopardy_json_file = open(path.join(project_root, 'support_files', 'JEOPARDY_QUESTIONS1.json')).read()
        filtered_question_list = self.filter_questions(
            json.loads(jeopardy_json_file),
            banned_categories=Question.banned_categories,
            banned_phrases=Question.banned_phrases,
        )
        for question_json in filtered_question_list:
            text, valid_links = self.separate_html(question_json['question'])
            new_question = Question(
                text=text,
                value=self.convert_value_to_int(question_json['value']),
                category=question_json['category'],
                daily_double=self.is_daily_double(self.value),
                answer=question_json['answer'],
                valid_links=json.dumps(valid_links),
                air_date=datetime.datetime.strptime(question_json['air_date'], '%Y-%m-%d').date()
            )

    def to_json(self) -> dict:
        question_dict = {
            'question': self.question,
            'valid_links': self.valid_links,
            'value': self.value,
            'category': self.category,
            'daily_double': self.daily_double,
            'answer': self.answer,
            'air_date': self.air_date
        }
        return question_dict


# class Room(models.Model):
#     players = models.ForeignKey(Player, validators=[room_is_full()])