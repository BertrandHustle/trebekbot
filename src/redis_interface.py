import json

from redis import Redis


class RedisInterface:
    def __init__(self, hostname='localhost', port=6379, db=0):
        self.redis_connection = Redis(host=hostname, port=port, db=db)

    def set_active_question(self, question: dict):
        return self.redis_connection.set('active_question', json.dumps(question))

    #TODO: rename this to reflect that it returns a json string, not a Question object
    def get_active_question(self):
        return self.redis_connection.get('active_question')

    def add_player(self, player: str):
        return self.redis_connection.sadd('active_players', player)

    def remove_player(self, player: str):
        return self.redis_connection.srem('active_players', player)

    def get_all_players(self) -> list:
        return [b.decode() for b in self.redis_connection.smembers('active_players')]
    