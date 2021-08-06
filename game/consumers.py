# Native
import json
# Third Party
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# Project
from game.models import Player
from src.judge import Judge
from src.redis_interface import RedisInterface


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

    def receive(self, text_data):
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
