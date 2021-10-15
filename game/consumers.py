# Native
import asyncio
import json
from random import randint
# Third Party
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
# Project
from game.models import Player, Question
from src.judge import Judge
from src.redis_interface import RedisInterface


class TimerConsumer(AsyncWebsocketConsumer):

    #TODO: have this report timer ticks back to client
    async def _create_timer(self, time_limit):
        await asyncio.sleep(time_limit)
        await self.send(text_data='Timer Up!')

    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        time_limit = 60
        timer_task = asyncio.create_task(self._create_timer(time_limit))
        if text_data == 'kill timer':
            timer_task.cancel()


class QuestionConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        if text_data == 'get_question':
            # get random question
            question_count = Question.objects.count()
            rand_question = Question.objects.get(pk=randint(0, question_count))
            question_json = {
                'text': rand_question.text,
                'valid_links': rand_question.valid_links,
                'value': rand_question.value,
                'category': rand_question.category,
                'daily_double': rand_question.daily_double,
                'answer': rand_question.answer,
                'date': rand_question.date
            }
            # DEBUG
            print(rand_question.answer)
            self.send(json.dumps(question_json))


class AnswerConsumer(WebsocketConsumer):
    judge = Judge()
    redis_helper = RedisInterface()

    def connect(self):
        self.room_group_name = 'test_room'
        self.redis_helper.add_player(self.scope['user'].username)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()
        # Update page with new list of players
        self.send(
            json.dumps(
                {
                    'type': 'player_login',
                    'player': self.scope['user'].username
                }
            )
        )

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        if text_data.get('buzzer'):
            # Get player so we know who buzzed in
            self.send(text_data=json.dumps({
                'player': Player.objects.get(user=self.scope['user']),
                'type': 'buzzer'
                }
            ))
        else:
            text_data_json = json.loads(text_data)
            given_answer = text_data_json['givenAnswer']
            correct_answer = text_data_json['correctAnswer']
            question_value = text_data_json['questionValue']
            response, correct, player_score = self.eval_answer(given_answer, correct_answer, question_value)

            # Send message to room group
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'answer_result',
                    'response': response,
                    'correct': correct,
                    'player_score': player_score
                }
            )

    def answer_result(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps({
             'response': event['response'],
             'correct': event['correct'],
             'player_score': event['player_score']
        }))

    def eval_answer(self, given_answer, correct_answer, question_value):
        player = Player.objects.get(user=self.scope['user'])
        question_value = int(question_value)
        response, correct = '', False
        answer_is_correct = self.judge.fuzz_answer(given_answer, correct_answer)
        if answer_is_correct == 'close':
            response = self.judge.check_closeness(given_answer, correct_answer)
        elif answer_is_correct:
            response = 'That is correct. The answer is ' + given_answer
            correct = True
            player.score += question_value
            player.save()
        elif not answer_is_correct:
            response = 'Sorry, that is incorrect.'
            correct = False
            player.score -= question_value
            player.save()
        return response, correct, player.score
