# Native
import os
import urllib.parse as urlparse
from contextlib import suppress
# Third-party
import psycopg2
# Project

'''
Class for database setup/functions
This will primarily serve to store players and track their scores/money totals
:param filename: name of database file
:param filepath: path to persistant storage where db is to be located
:param connection: connection object to database
'''


class db:
    """
    db object for interacting with psql database
    """
    def __init__(self):
        # Use local db if we're doing development
        try:
            result = urlparse.urlparse(os.environ['DATABASE_URL'])
            dbname = result.path[1:]
            dbuser = result.dbuser
            password = result.password
            dbhost = result.hostname
        except KeyError:
            dbname = 'django'
            dbuser = 'postgres'
            password = 'test'
            dbhost = '127.0.0.1'
        self.conn_string = 'dbname=' + dbname + ' ' + \
            'user=' + dbuser + ' ' + \
            'password=' + password + ' ' + \
            'host=' + dbhost + ' '
        self.connection = psycopg2.connect(self.conn_string)
        self.connection.commit()

    # tells us what the given player's score is
    def get_score(self, connection, player):
        cursor = connection.cursor()
        select_score = cursor.execute(
            '''
            SELECT SCORE FROM playerS WHERE NAME = %s
            ''',
            (player,)
        )
        results = cursor.fetchall()
        # TODO: make this more elegant
        if results:
            return results[0][0]

    # gets top ten scorers from database
    def return_top_ten(self, connection):
        cursor = connection.cursor()
        top_ten = cursor.execute(
            '''
            SELECT * FROM playerS ORDER BY SCORE DESC LIMIT 10
            ''',
        )
        top_ten = cursor.fetchall()
        return top_ten

    # gets player with most wins
    def return_all_time_champ(self, connection):
        cursor = connection.cursor()
        champion_search = cursor.execute(
            '''
            SELECT NAME, MAX(WINS) FROM playerS
            '''
        ).fetchall()
        return champion_search[0][0], champion_search[0][1]

    # gets champion (highest scorer) from database
    def get_champion(self, connection):
        cursor = connection.cursor()
        champion_search = cursor.execute(
            '''
            SELECT NAME, SCORE FROM playerS WHERE
            SCORE = (SELECT MAX(SCORE) FROM playerS)
            '''
        )
        champion_search = cursor.fetchall()
        with suppress(IndexError):
            champion_name = champion_search[0][0]
            champion_score = champion_search[0][1]
            if champion_score > 0:
                return champion_name, champion_score

    '''
    updates the score of a given player
    :param score_change: the amount by which we will change the player's score
    '''
    def update_score(self, connection, player, score_change):
        try:
            cursor = connection.cursor()
            cursor.execute(
                '''
                UPDATE playerS
                SET SCORE = CASE
                    WHEN (SCORE + %s) <= -10000 THEN -10000
                    ELSE SCORE + %s
                END
                WHERE NAME = %s
                ''', (int(score_change), int(score_change), player)
            )
            self.connection.commit()
        except ValueError:
            pass

    # adds 1 to a player's wins
    def increment_win(self, connection, player):
        cursor = connection.cursor()
        cursor.execute(
            '''
            UPDATE playerS
            SET WINS = WINS + 1
            WHERE NAME = %s
            ''', (player,)
        )
        self.connection.commit()

    # shows all-time wins for player
    def get_player_wins(self, connection, player):
        cursor = connection.cursor()
        wins = cursor.execute(
            '''
            SELECT WINS FROM playerS WHERE NAME = %s
            ''',
            (player,)
        )
        wins = cursor.fetchall()
        if wins:
            return wins[0][0]

    # resets scores to 0 for all players, used for nightly resets
    def wipe_scores(self, connection):
        cursor = connection.cursor()
        cursor.execute(
            '''
            UPDATE playerS SET SCORE = 0
            '''
        )
        self.connection.commit()
