import json

from redis import Redis


class RedisInterface:
    def __init__(self, hostname='localhost', port=6379, db=0):
        self.redis_connection = Redis(host=hostname, port=port, db=db)

    def set_active_question(self, question: str):
        try:
            json.loads(question)
        except ValueError:
            raise ValueError('Question must be a string representation of a valid json object.')
        return self.redis_connection.set('active_question', question)

    def get_active_question(self):
        return self.redis_connection.get('active_question')

    def add_player(self, player: str):
        return self.redis_connection.sadd('active_players', player)

    def remove_player(self, player: str):
        return self.redis_connection.srem('active_players', player)

    def get_all_players(self) -> list:
        return [b.decode() for b in self.redis_connection.smembers('active_players')]
    