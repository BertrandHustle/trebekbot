# Third Party
from redis import Redis


class RedisInterface:
    def __init__(self, hostname='localhost', port=6379, db=0):
        self.redis_connection = Redis(host=hostname, port=port, db=db)

    def add_player(self, player: str):
        self.redis_connection.sadd('active_players', player)

    def remove_player(self, player: str):
        self.redis_connection.srem('active_players', player)