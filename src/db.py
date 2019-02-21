import psycopg2
import pdb
from os import path, environ

'''
Class for database setup/functions
This will primarily serve to store users and track their scores/money totals
:param filename: name of database file
:param filepath: path to persistant storage where db is to be located
:param connection: connection object to database
'''

'''
# heroku postgres database url
DATABASE_URL = environ['DATABASE_URL']
'''

class db(object):
    def __init__(self, db_name, host, port, user):
        self.db_name = db_name
        self.host = host
        self.port = port
        self.user = user
        self.connection = self.create_connection(
            self.db_name,
            self.host,
            self.port,
            self.user
        )
        self.create_table_users(self.connection)
        self.connection.commit()

    def create_connection(self, db_name, host, port, user):
        return psycopg2.connect(
            database=db_name,
            host=host,
            port=port,
            user=user
        )

    '''
    :param connection: connection to the sql database
    :sql_param name: name of user
    :sql_param score: current money value of user
    :sql_param champion_score: leader's score (for persistence between resets)
    :sql_param champion: flag if user was the champion before reboot
    :sql_param wins: total all-time wins
    '''

    def create_table_users(self, connection):
        cursor = connection.cursor()
        # TODO: Fix this to avoid injection attacks
        cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
        id serial,
        name text NOT NULL UNIQUE,
        score integer NOT NULL DEFAULT 0,
        champion_score integer NOT NULL DEFAULT 0,
        champion integer DEFAULT 0,
        wins integer DEFAULT 0
        );
        '''
        )
        # save changes to db
        self.connection.commit()

    def drop_table_users(self, connection):
        cursor = connection.cursor()
        cursor.execute(
        '''
        DROP TABLE users;
        '''
        )
        return 1
        # save changes to db
        self.connection.commit()

    # add user if they don't already exist in the database
    def add_user_to_db(self, connection, user):
        cursor = connection.cursor()
        cursor.execute(
        '''
        INSERT INTO USERS(name) VALUES(%s) ON CONFLICT(name) DO NOTHING;
        ''',
        (user,)
        )
        # save changes to db
        self.connection.commit()

    # tells us what the given user's score is
    def get_score(self, connection, user):
        cursor = connection.cursor()
        select_score = cursor.execute(
        '''
        SELECT SCORE FROM USERS WHERE NAME = %s
        ''',
        (user,)
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
        SELECT * FROM USERS ORDER BY SCORE DESC LIMIT 10
        ''',
        )
        top_ten = cursor.fetchall()
        return top_ten

    # gets user with most wins
    def return_all_time_champ(self, connection):
        cursor = connection.cursor()
        champion_search = cursor.execute(
        '''
        SELECT NAME, MAX(WINS) FROM USERS
        '''
        ).fetchall()
        return champion_search[0][0], champion_search[0][1]

    # gets champion (highest scorer) from database
    def get_champion(self, connection):
        cursor = connection.cursor()
        champion_search = cursor.execute(
        '''
        SELECT NAME, SCORE FROM USERS WHERE
        SCORE = (SELECT MAX(SCORE) FROM USERS)
        '''
        )
        champion_search = cursor.fetchall()
        champion_name = champion_search[0][0]
        champion_score = champion_search[0][1]
        if champion_score > 0:
            return champion_name, champion_score

    # TODO: get rid of this and set_champion, both are unnecessary since we
    # have a persistant database now

    # same as above, but gets champion_score (last night's score)
    # instead of current score
    def get_last_nights_champion(self, connection):
        cursor = connection.cursor()
        champion_search = cursor.execute(
        '''
        SELECT NAME, CHAMPION_SCORE FROM USERS WHERE
        CHAMPION_SCORE = (SELECT MAX(CHAMPION_SCORE) FROM USERS)
        '''
        )
        champion_search = cursor.fetchall()
        pdb.set_trace()
        return champion_search[0][0], champion_search[0][1]

    # sets champion before nightly reset
    # TODO: this needs to store score as well as username
    def set_champion(self, connection, user, score):
        cursor = connection.cursor()
        # set all champions to 0 first to ensure we don't have multiple champs
        cursor.execute(
        '''
        UPDATE USERS SET CHAMPION = 0
        '''
        )
        cursor.execute(
        '''
        UPDATE USERS SET CHAMPION = 1, CHAMPION_SCORE = %s WHERE NAME = %s
        ''',
        (score, user)
        )
        self.connection.commit()

    '''
    updates the score of a given user
    :param score_change: the amount by which we will change the user's score
    '''
    def update_score(self, connection, user, score_change):
        cursor = connection.cursor()
        cursor.execute(
        '''
        UPDATE USERS
        SET SCORE = CASE
            WHEN (SCORE + %s) <= -10000 THEN -10000
            ELSE SCORE + %s
        END
        WHERE NAME = %s
        ''', (score_change, score_change, user)
        )
        self.connection.commit()

    # adds 1 to a user's wins
    def increment_win(self, connection, user):
        cursor = connection.cursor()
        cursor.execute(
        '''
        UPDATE USERS
        SET WINS = WINS + 1
        WHERE NAME = %s
        ''', (user,)
        )
        self.connection.commit()

    # shows all-time wins for user
    def get_user_wins(self, connection, user):
        cursor = connection.cursor()
        wins = cursor.execute(
        '''
        SELECT WINS FROM USERS WHERE NAME = %s
        ''',
        (user,)
        )
        wins = cursor.fetchall()
        if wins:
            return wins[0][0]

    # resets scores to 0 for all users, used for nightly resets
    def wipe_scores(self, connection):
        cursor = connection.cursor()
        cursor.execute(
        '''
        UPDATE USERS SET SCORE = 0
        '''
        )
        self.connection.commit()

    # resets champion_scores to 0 for all users, used for nightly resets
    def wipe_champion_scores(self, connection):
        cursor = connection.cursor()
        cursor.execute(
        '''
        UPDATE USERS SET CHAMPION_SCORE = 0
        '''
        )
        self.connection.commit()
