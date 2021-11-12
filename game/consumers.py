# Native
import asyncio
import json
from contextlib import suppress
from random import randint
# Third Party
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer, JsonWebsocketConsumer, WebsocketConsumer
from channels.layers import get_channel_layer
# Project
from game.models import Player, Question
from src.judge import Judge
from src.redis_interface import RedisInterface


class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'game_{self.room_name}'

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

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


class TimerConsumer(AsyncWebsocketConsumer):

    #TODO: have this report timer ticks back to client
    async def _create_timer(self, time_limit):
        await asyncio.sleep(time_limit)
        await self.send(text_data='Timer Up!')

    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        timer_task = None
        if text_data == 'start_timer':
            time_limit = 60
            timer_task = asyncio.create_task(self._create_timer(time_limit))
            await self.send(text_data='Timer Started!')
        if text_data == 'kill_timer':
            # ignore errors where task isn't created yet
            with suppress(AttributeError):
                timer_task.cancel()


class BuzzerConsumer(WebsocketConsumer):

    buzzer_locked = False
    buzzed_in_player = ''
    
    def connect(self):
        async_to_sync(self.channel_layer.group_add)('buzzer', self.channel_name)
        async_to_sync(self.channel_layer.group_send)('game_test', {'type': 'room.message', 'text': 'test'})
        self.accept()

    # TODO: return player name who buzzed in
    def receive(self, text_data=None, bytes_data=None):
        if text_data == 'status':
            self.send(text_data=BuzzerConsumer.buzzer_locked)
        elif text_data == 'buzz_in':
            if not BuzzerConsumer.buzzer_locked:
                BuzzerConsumer.buzzer_locked = True
                self.send(text_data='buzzed_in')
            else:
                self.send(text_data='buzzer_locked')
        elif text_data == 'reset_buzzer':
            BuzzerConsumer.buzzer_locked = False
        elif text_data.startswith('buzzed_in_player:'):
            BuzzerConsumer.buzzed_in_player = text_data.split(':')[1]
            self.send(text_data='buzzed_in_player:' + BuzzerConsumer.buzzed_in_player)

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)('buzzer', self.channel_name)


class QuestionConsumer(WebsocketConsumer):

    live_question = Question()

    def connect(self):
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
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


class AnswerConsumer(JsonWebsocketConsumer):
    judge = Judge()

    def connect(self):
        self.accept()

    def receive_json(self, text_data=None, bytes_data=None):
        given_answer = text_data['givenAnswer']
        correct_answer = text_data['correctAnswer']
        question_value = text_data['questionValue']
        response, correct, player_score = self.eval_answer(given_answer, correct_answer, question_value)
        payload = {
            'type': 'answer_result',
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



