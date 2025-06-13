from __future__ import annotations

import re
import random
from collections import Counter
from contextlib import suppress

from requests import get as get_http_code
from requests.exceptions import RequestException

from django.db import models
from django.db.models import Count, Min, Q
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

    air_date = models.DateField()
    answer = models.CharField(max_length=250)
    category = models.CharField(max_length=100)
    daily_double = models.BooleanField(default=False)
    round = models.CharField(null=True, blank=True)
    text = models.CharField(max_length=750)
    valid_links = ArrayField(
        models.CharField(max_length=250, blank=True),
        size=3,
        default=list
    )
    value = models.IntegerField()

    def __str__(self):
        return f'{self.category} | {self.value} | {self.air_date} | {self.text}'

    banned_categories = 'missing this category'

    @staticmethod
    def _calculate_category_score_range(questions: list[Question], num_questions: int = 5) -> set:
        """
        calculate the missing score for a category missing a question
        used to find candidates if a category is missing a question
        """
        scores = sorted([q.value for q in questions])
        score_deltas = []
        for ix, score in enumerate(scores):
            try:
                score_deltas.append(scores[ix+1]-score)
            except IndexError:
                break
        most_common_delta = Counter(score_deltas).most_common(1)[0][0]
        score_list = [i*most_common_delta for i in range(1,num_questions)]
        return set(score_list).difference(scores)


    @staticmethod
    def get_random_question() -> Question:
        """
        gets a random question from the db and filters out unwanted categories
        :return: Question
        """
        valid_questions = Question.objects.filter(~Q(category__in=Question.banned_categories))
        return random.choice(valid_questions)

    @staticmethod
    def get_daily_double() -> Question:
        """
        gets a random daily double question (for testing)
        :return: Question
        """
        valid_questions = Question.objects.filter(~Q(category__in=Question.banned_categories) & Q(daily_double=True))
        return random.choice(valid_questions)

    @staticmethod
    def get_question_with_valid_links() -> Question:
        """
        gets a random question with valid links (for testing)
        :return: Question
        """
        valid_questions = Question.objects.filter(~Q(category__in=Question.banned_categories) & ~Q(valid_links=[]))
        return random.choice(valid_questions)

    def get_value(self):
        return '$' + str(self.value)


    #TODO: filter out seen here/heard here
    #TODO: make anomalous values daily doubles
    #TODO: standardize on point value increases
    @staticmethod
    def get_random_category(
        excluded_categories: list = None,
        min_value = 100,
        num_questions: int = 5,
        round: str = 'Jeopardy!'
    ) -> tuple[list[Question], str] or (None, None):
        """
        gets a random category of <num_questions> questions
        :param excluded_categories: categories to exclude if they turn up in random choice
        :param min_value: minimum dollar value that a question can have in a category
        :param num_questions: how many questions to retrieve for a given category
        :param round: which round of questions to retrieve (Jeopardy!, Double Jeopardy!, or Final Jeopardy!)
        :return: list of questions belonging to common category
        """
        category_count = (Question.objects.filter(round=round)
                          .values('category')
                          .annotate(min_value=Min('value'), total=Count('category')))
        if not excluded_categories:
            excluded_categories = []
        filtered_categories = [
            cat['category'] for cat in category_count
            if cat['total'] >= num_questions and cat['category'] not in excluded_categories
            and cat['min_value'] == min_value
        ]
        # TODO: do something about questions with no round
        random_category = random.choice(filtered_categories)
        random_questions = Question.objects.filter(
            category=random_category, round=round
        ).distinct('value')[:num_questions]  # distinct SHOULD do the sorting on value for free
        missing_scores = Question._calculate_category_score_range(random_questions)
        if len(random_questions) < num_questions or missing_scores:
            print(random_questions.values_list('value', flat=True))
            random_questions = list(random_questions)
            for missing_score in missing_scores:
                fill_in_question = Question.objects.filter(
                    category=random_category,
                    round__iexact=round,
                    value=missing_score
                ).first()
                if not fill_in_question:
                    return None, None
                else:
                    random_questions.pop()
                    random_questions.append(fill_in_question)

        return sorted(random_questions, key=lambda question: question.value), random_category

    @staticmethod
    def convert_value_to_int(value) -> int:
        """
        removes $ and commas from question values, e.g. '$2,500'
        :param value: string representation of dollar value
        :return: int of value
        """
        try:
            # remove special characters if this is a string
            if type(value) is str:
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
