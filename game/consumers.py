# Native
import json
# Third Party
from channels.generic.websocket import WebsocketConsumer
# Project
from src.judge import Judge


class AnswerConsumer(WebsocketConsumer):
    judge = Judge()

    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        given_answer = text_data_json['givenAnswer']
        correct_answer = text_data_json['correctAnswer']
        result = self.judge.fuzz_answer(given_answer, correct_answer)
        self.send(text_data=json.dumps({
            'result': result
        }))