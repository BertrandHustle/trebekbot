import json
from contextlib import suppress
from datetime import date, datetime
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management.base import BaseCommand

from game.models import Question
from paths import ROOT_DIR


class Command(BaseCommand):
    help = 'add round field to Questions'

    def handle(self, *args, **options):
        with open(Path(ROOT_DIR, 'support_files', 'JEOPARDY_QUESTIONS1.json')) as jeopardy_json:
            for question_json in json.load(jeopardy_json):
                air_date_str = question_json['air_date']
                air_datetime = datetime.strptime(air_date_str, '%Y-%m-%d')
                air_date = date(air_datetime.year, air_datetime.month, air_datetime.day)
                with suppress(ObjectDoesNotExist, MultipleObjectsReturned):
                    question = Question.objects.get(text=question_json['question'], air_date=air_date)
                    question.round = question_json['round']
                    question.save()
                    print(question)