from __future__ import annotations

import operator
import re
import random
from contextlib import suppress
from functools import reduce

from requests import get as get_http_code
from requests.exceptions import RequestException

from django.db import models
from django.db.models import Q
from django.contrib.postgres.fields import ArrayField


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
    valid_links = ArrayField(
        models.CharField(max_length=250, blank=True),
        size=3,
        default=list
    )
    air_date = models.DateField()

    def __str__(self):
        return f'{self.category} | {self.value} | {self.air_date} | {self.text}'

    banned_categories = 'missing this category'
    banned_phrases = ['seen here', 'heard here', 'audio clue']

    @staticmethod
    def get_random_question() -> Question:
        """
        gets a random question from the db and filters out unwanted categories and phrases
        :return: Question
        """
        pks = Question.objects.exclude(
            reduce(operator.and_, (Q(text__contains=phrase) for phrase in Question.banned_phrases)),
            category__in=Question.banned_categories
        ).values_list('pk', flat=True)
        return Question.objects.get(pk=random.choice(pks))

    @staticmethod
    def get_daily_double() -> Question:
        """
        gets a random daily double question (for testing)
        :return: Question
        """
        pks = Question.objects.filter(
            reduce(operator.and_, (~Q(text__contains=phrase) for phrase in Question.banned_phrases)) &
            ~Q(category__in=Question.banned_categories) &
            Q(daily_double=True)
        ).values_list('pk', flat=True)
        return Question.objects.get(pk=random.choice(pks))

    @staticmethod
    def get_question_with_valid_links() -> Question:
        """
        gets a random question with valid links (for testing)
        :return: Question
        """
        pks = Question.objects.filter(
            reduce(operator.and_, (~Q(text__contains=phrase) for phrase in Question.banned_phrases)) &
            ~Q(category__in=Question.banned_categories) &
            ~Q(valid_links=[])
        ).values_list('pk', flat=True)
        return Question.objects.get(pk=random.choice(pks))

    def get_value(self):
        return '$' + str(self.value)

    @staticmethod
    def convert_value_to_int(value) -> int:
        """
        removes $ and commas from question values, e.g. '$2,500'
        :param value: string representation of dollar value
        :return: int of value
        """
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
    def separate_html(question_text) -> tuple or str:
        """
        separates html links from questions
        :param question_text: content of given question
        :return: tuple of the question text and link if link is valid, otherwise just returns the text
        """
        with suppress(RequestException):
            # scrub newline chars from question text
            question_text = re.sub(r'\n', '', question_text)
            # valid links to return
            valid_links = []
            # use regex to check in case link syntax got mangled
            regex_links = re.findall(r'https?://.*?\"', question_text)
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

