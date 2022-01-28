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


def init_stateful_objects(channel_name: str):
    redis_interfacer.hset(f'{get_shared_channel_name(channel_name)}', 'buzzer_locked', 0)
    redis_interfacer.hset(f'{get_shared_channel_name(channel_name)}', 'buzzed_in_player', '')
    redis_interfacer.hset(f'{get_shared_channel_name(channel_name)}', 'timer', 0)
    # TODO: this will need to be converted into a json/some data structure
    redis_interfacer.hset(f'{get_shared_channel_name(channel_name)}', 'live_question', '')


def remove_stateful_objects(channel_name: str):
    redis_interfacer.hdel(f'{get_shared_channel_name(channel_name)}', 'buzzer_locked')
    redis_interfacer.hdel(f'{get_shared_channel_name(channel_name)}', 'buzzed_in_player')
    redis_interfacer.hdel(f'{get_shared_channel_name(channel_name)}', 'timer')
    redis_interfacer.hdel(f'{get_shared_channel_name(channel_name)}', 'live_question')


class RoomConsumer(WebsocketConsumer):

    def connect(self):
        init_stateful_objects(self.channel_name)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        # Join room group
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()

    def room_message(self, event):
        print('received!')
        self.send(text_data=event["text"])

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        remove_stateful_objects(self.channel_name)


class TimerConsumer(AsyncJsonWebsocketConsumer):

    async def tick_redis_timer(self):
        redis_interfacer.hincrby(f'{get_shared_channel_name(self.channel_name)}', 'timer', -1)

    def get_redis_timer_value(self):
        return int(redis_interfacer.hget(get_shared_channel_name(self.channel_name), 'timer').decode())

    def set_redis_timer_value(self, time_limit):
        redis_interfacer.hset(get_shared_channel_name(self.channel_name), 'timer', time_limit)

    def reset_redis_timer(self):
        redis_interfacer.hset(f'{get_shared_channel_name(self.channel_name)}', 'timer', 0)

    async def _tick_timer(self, time_limit):
        self.set_redis_timer_value(time_limit)
        while self.get_redis_timer_value() > 0:
            await asyncio.sleep(1)
            await self.tick_redis_timer()
            await self.send_json({'message': 'tick'})
        self.reset_redis_timer()

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        await self.accept()

    async def receive_json(self, content, **kwargs):
        content = content.replace('"', '')
        timer_task = None
        if content == 'start_timer':
            time_limit = 60
            timer_task = asyncio.create_task(self._tick_timer(time_limit))
            await self.send_json({'message': 'Timer Started!'})
        if content == 'kill_timer':
            # ignore errors where task isn't created yet
            with suppress(AttributeError):
                timer_task.cancel()


class BuzzerConsumer(WebsocketConsumer):

    def get_buzzer_status(self):
        return int(redis_interfacer.hget(get_shared_channel_name(self.channel_name), 'buzzer_locked').decode())

    def set_buzzer_status(self, status: int):
        # use 0 for False, 1 for True
        redis_interfacer.hset(get_shared_channel_name(self.channel_name), 'buzzer_locked', status)

    def get_buzzed_in_player(self):
        return redis_interfacer.hget(get_shared_channel_name(self.channel_name), 'buzzed_in_player').decode()

    def set_buzzed_in_player(self, player: str):
        redis_interfacer.hset(get_shared_channel_name(self.channel_name), 'buzzed_in_player', player)
    
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        async_to_sync(self.channel_layer.group_add)('question', self.channel_name)
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        if text_data == 'status':
            self.send(text_data=self.get_buzzed_in_player())
        elif text_data == 'buzz_in':
            print(self.get_buzzer_status())
            if self.get_buzzer_status():
                self.send(text_data='buzzer_locked')
            else:
                self.set_buzzer_status(1)
                self.send(text_data='buzzed_in')
        elif text_data == 'reset_buzzer':
            self.set_buzzer_status(0)
        elif text_data.startswith('buzzed_in_player:'):
            self.set_buzzed_in_player(text_data.split(':')[1])
            self.send(text_data='buzzed_in_player:' + self.get_buzzed_in_player())

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)('buzzer', self.channel_name)


class QuestionConsumer(WebsocketConsumer):

    live_question = Question()

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'
        self.channel_layer.group_add('question', self.channel_name)
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        # for some reason JSON.stringify adds double quotes
        text_data = text_data.replace('"', '')
        if text_data == 'get_question':
            # get random question
            question_count = Question.objects.count()
            QuestionConsumer.live_question = Question.objects.get(pk=randint(0, question_count))
            question_json = {
                'text': QuestionConsumer.live_question.text,
                'valid_links': QuestionConsumer.live_question.valid_links,
                'value': QuestionConsumer.live_question.value,
                'category': QuestionConsumer.live_question.category,
                'daily_double': QuestionConsumer.live_question.daily_double,
                'answer': QuestionConsumer.live_question.answer,
                'date': QuestionConsumer.live_question.date
            }
            # DEBUG
            print(QuestionConsumer.live_question.answer)
            self.send(json.dumps(question_json))
        elif text_data == 'question_status':
            self.send(bool(QuestionConsumer.live_question))
        elif text_data == 'reset_question':
            QuestionConsumer.live_question = False

    async def disconnect(self, close_code):
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
        "timer": TimerConsumer.as_asgi(),
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
