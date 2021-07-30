from fakeredis import FakeStrictRedis
import pytest
from src.redis_interface import RedisInterface


# overwrite init to avoid having to provide real Redis connection creds
class FakeRedisInterface(RedisInterface):
    def __init__(self):
        self.redis_connection = FakeStrictRedis()


test_redis = FakeRedisInterface()
test_players = ['test', 'test2', 'test3']


@pytest.fixture
def populate_redis():
    for player in test_players:
        test_redis.add_player(player)


def test_get_all_players(populate_redis):
    assert all(x in test_players for x in test_redis.get_all_players())


def test_remove_players(populate_redis):
    for player in test_players[:-1]:
        test_redis.remove_player(player)
    player_list = test_redis.get_all_players()
    assert 'test3' in player_list
    assert any(x not in test_players[:1] for x in player_list)