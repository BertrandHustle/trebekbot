# Native
import json
# Third Party
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
# Project
from src.judge import Judge


class AnswerConsumer(WebsocketConsumer):
    judge = Judge()

    def connect(self):
        self.room_group_name = 'test_room'

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

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
        result = self.judge.fuzz_answer(given_answer, correct_answer)

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'answer_result',
                'result': result
            }
        )

    def answer_result(self, event):
        result = event['result']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
             'result': result
        }))

    def judge_answer(self, given_answer, correct_answer):
        player = Player.objects.get(user=self.scope['user'])
        given_answer = request.POST.get('givenAnswer')
        correct_answer = request.POST.get('correctAnswer')
        question_value = int(request.POST.get('questionValue'))
        answer_result = {'result': '', 'text': '', 'player_score': 0}
        answer_is_correct = answer_checker.fuzz_answer(given_answer, correct_answer)
        if answer_is_correct == 'close':
            answer_result['text'] = answer_checker.check_closeness(given_answer, correct_answer)
        elif answer_is_correct:
            answer_result['text'] = 'That is correct. The answer is ' + given_answer
            answer_result['result'] = True
            player.score += question_value
            player.save()
        elif not answer_is_correct:
            answer_result['text'] = 'Sorry, that is incorrect.'
            answer_result['result'] = False
            player.score -= question_value
            player.save()
        answer_result['player_score'] = player.score
        return JsonResponse(answer_result)
