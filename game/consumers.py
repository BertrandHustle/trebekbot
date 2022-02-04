# Native
import asyncio
import json
from contextlib import suppress
from random import randint
# Third Party
from channelsmultiplexer import AsyncJsonWebsocketDemultiplexer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer, WebsocketConsumer
# Project
from game.models import Player, Question
from src.judge import Judge
from src.redis_interface import RedisInterface

redis_interfacer = RedisInterface().redis_connection


def get_shared_channel_name(channel_name: str):
    return channel_name.split('!')[0]


class BuzzerConsumer(AsyncJsonWebsocketConsumer):

    def init_buzzer(self):
        redis_interfacer.hset(f'{get_shared_channel_name(self.channel_name)}', 'buzzer_locked', 0)
        redis_interfacer.hset(f'{get_shared_channel_name(self.channel_name)}', 'buzzed_in_player', '')

    def remove_buzzer(self):
        redis_interfacer.hdel(f'{get_shared_channel_name(self.channel_name)}', 'buzzer_locked')
        redis_interfacer.hdel(f'{get_shared_channel_name(self.channel_name)}', 'buzzed_in_player')

    def get_buzzer_status(self):
        return int(redis_interfacer.hget(get_shared_channel_name(self.channel_name), 'buzzer_locked').decode())

    def set_buzzer_status(self, status: int):
        # use 0 for False, 1 for True
        redis_interfacer.hset(get_shared_channel_name(self.channel_name), 'buzzer_locked', status)

    def get_buzzed_in_player(self):
        return redis_interfacer.hget(get_shared_channel_name(self.channel_name), 'buzzed_in_player').decode()

    def set_buzzed_in_player(self, player: str):
        redis_interfacer.hset(get_shared_channel_name(self.channel_name), 'buzzed_in_player', player)
    
    async def connect(self):
        self.init_buzzer()
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        await self.channel_layer.group_add('question', self.channel_name)
        await self.accept()

    async def receive_json(self, text_data=None, bytes_data=None):
        if text_data == 'status':
            await self.send(text_data=self.get_buzzed_in_player())
        elif text_data == 'buzz_in':
            print(self.get_buzzer_status())
            if self.get_buzzer_status():
                await self.send(text_data='buzzer_locked')
            else:
                self.set_buzzer_status(1)
                await self.send(text_data='buzzed_in')
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'send_message',
                    'message': 'buzzed_in',
                    'event': "buzzer"
                })
        elif text_data == 'reset_buzzer':
            self.set_buzzer_status(0)
        elif text_data.startswith('buzzed_in_player:'):
            self.set_buzzed_in_player(text_data.split(':')[1])
            await self.send(text_data='buzzed_in_player:' + self.get_buzzed_in_player())

    def disconnect(self, close_code):
        self.remove_buzzer()
        async_to_sync(self.channel_layer.group_discard)('buzzer', self.channel_name)

    async def send_message(self, res):
        # Send message to WebSocket
        await self.send_json({"payload": res})


class QuestionConsumer(AsyncJsonWebsocketConsumer):

    def init_question(self):
        # TODO: this will need to be converted into a json/some data structure
        redis_interfacer.hset(f'{get_shared_channel_name(self.channel_name)}', 'live_question', '')

    def remove_question(self):
        redis_interfacer.hdel(f'{get_shared_channel_name(self.channel_name)}', 'live_question')

    def get_question(self):
        redis_interfacer.hget(f'{get_shared_channel_name(self.channel_name)}', 'live_question')

    async def connect(self):
        self.init_question()
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        self.channel_layer.group_add('question', self.channel_name)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        # for some reason JSON.stringify adds double quotes
        content = content.replace('"', '')
        if content == 'get_question':
            # get random question
            question_count = Question.objects.count()
            live_question = Question.objects.get(pk=randint(0, question_count))
            question_json = {
                'text': live_question.text,
                'valid_links': live_question.valid_links,
                'value': live_question.value,
                'category': live_question.category,
                'daily_double': live_question.daily_double,
                'answer': live_question.answer,
                'date': live_question.date
            }
            await self.send_json(question_json)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send_message',
                'message': live_question,
                'event': 'question'
            })
            # DEBUG
            print(live_question.answer)
        elif content == 'question_status':
            await self.send_json(bool(self.get_question()))
        elif content == 'reset_question':
            self.init_question()

    async def disconnect(self, close_code):
        self.remove_question()
        await self.channel_layer.group_discard('question', self.channel_name)


class AnswerConsumer(JsonWebsocketConsumer):
    judge = Judge()

    def connect(self):
        async_to_sync(self.channel_layer.group_add)('answer', self.channel_name)
        self.accept()

    def receive_json(self, text_data=None, bytes_data=None):
        given_answer = text_data['givenAnswer']
        correct_answer = text_data['correctAnswer']
        question_value = text_data['questionValue']
        response, correct, player_score = self.eval_answer(given_answer, correct_answer, question_value)
        payload = {
            'type': 'answer',
            'response': response,
            'correct': correct,
            'player_score': player_score
        }
        self.send_json(payload)

    def eval_answer(self, given_answer, correct_answer, question_value):
        player = Player.objects.get(user=self.scope['user'])
        question_value = int(question_value)
        response, correct = '', False
        answer_is_correct = self.judge.fuzz_answer(given_answer, correct_answer)
        if answer_is_correct == 'close':
            response = self.judge.check_closeness(given_answer, correct_answer)
            correct = 'close'
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

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)('answer', self.channel_name)


class GameDemultiplexer(AsyncJsonWebsocketDemultiplexer):
    applications = {
        "buzzer": BuzzerConsumer.as_asgi(),
        "question": QuestionConsumer.as_asgi(),
        "answer": AnswerConsumer.as_asgi(),
    }



#         # Update page with new list of players
#         self.send(
#             json.dumps(
#                 {
#                     'type': 'player_login',
#                     'player': self.scope['user'].username
#                 }
#             )
#         )
#
