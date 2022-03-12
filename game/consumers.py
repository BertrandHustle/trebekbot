# Native
import json
from contextlib import suppress
from random import randint
# Third Party
from channelsmultiplexer import AsyncJsonWebsocketDemultiplexer
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
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

    #TODO: check if rest of connect func needs to be awaited
    async def connect(self):
        self.init_buzzer()
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        if content == 'status':
            await self.send(text_data=self.get_buzzed_in_player())
        elif content == 'buzz_in':
            if self.get_buzzer_status():
                await self.send_json(content='buzzer_locked')
            else:
                self.set_buzzer_status(1)
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'send.message',
                    'message': 'buzzed_in',
                    'event': "buzzer"
                })
        elif content == 'reset_buzzer':
            self.set_buzzer_status(0)
        elif content.startswith('buzzed_in_player:'):
            self.set_buzzed_in_player(content.split(':')[1])
            await self.send(text_data='buzzed_in_player:' + self.get_buzzed_in_player())

    async def disconnect(self, close_code):
        self.remove_buzzer()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_message(self, msg):
        # Send message to WebSocket
        await self.send_json(msg)


class QuestionConsumer(AsyncJsonWebsocketConsumer):

    def init_question(self):
        # TODO: this will need to be converted into a json/some data structure
        redis_interfacer.hset(f'{get_shared_channel_name(self.channel_name)}', 'live_question', '')

    def remove_question(self):
        redis_interfacer.hdel(f'{get_shared_channel_name(self.channel_name)}', 'live_question')

    def get_live_question(self):
        redis_interfacer.hget(f'{get_shared_channel_name(self.channel_name)}', 'live_question')

    def set_live_question(self, question_json):
        redis_interfacer.hset(
            f'{get_shared_channel_name(self.channel_name)}',
            'live_question',
            json.dumps(question_json)
        )

    @staticmethod
    @database_sync_to_async
    def get_new_question():
        # get random question
        question_count = Question.objects.count()
        return Question.objects.get(pk=randint(0, question_count))

    async def connect(self):
        self.init_question()
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        # for some reason JSON.stringify adds double quotes
        content = content.replace('"', '')
        if content == 'get_question':
            new_question = await self.get_new_question()
            question_json = {
                'text': new_question.text,
                'valid_links': new_question.valid_links,
                'value': new_question.value,
                'category': new_question.category,
                'daily_double': new_question.daily_double,
                'answer': new_question.answer,
                'date': new_question.date
            }
            self.set_live_question(question_json)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send.message',
                'message': question_json,
                'event': 'question',
            })
            # DEBUG
            print(question_json['answer'])
        elif content == 'question_status':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'send.message',
                'message': bool(self.get_live_question()),
                'event': 'question'
            })
        elif content == 'reset_question':
            self.init_question()

    async def disconnect(self, close_code):
        self.remove_question()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_message(self, msg):
        # Send message to WebSocket
        await self.send_json(msg)


class AnswerConsumer(AsyncJsonWebsocketConsumer):
    judge = Judge()

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def receive_json(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        given_answer = text_data['givenAnswer']
        correct_answer = text_data['correctAnswer']
        question_value = text_data['questionValue']
        response, correct, player_score = await self.eval_answer(given_answer, correct_answer, question_value)
        payload = {
            'type': 'answer',
            'response': response,
            'correct': correct,
            'player_score': player_score
        }
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'send.message',
            'message': payload,
            'event': 'answer',
        })


    @database_sync_to_async
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

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_message(self, msg):
        # Send message to WebSocket
        await self.send_json(msg)


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
