import sqlite3

'''
Class for database setup/functions
This will primarily serve to store users and track their scores/money totals
'''

# TODO: make sure users get initialized when they do anything w/trebekbot,
# not just answer a question

class db(object):

    def __init__(self, db_file):
        self.db_file = "database_files/" + db_file
        self.connection = self.create_connection(self.db_file)
        self.create_table_users(self.connection)
        self.connection.commit()

    def create_connection(self, db_file):
        return sqlite3.connect(db_file)

    '''
    :param connection: connection to the sql database
    :sql_param name: name of user
    :sql_param score: current money value of user
    '''

    # TODO: refactor from this:
    '''
    def create_table_users(self, connection):
        cursor = connection.cursor()
    '''
    # to this:
    '''
    @staticmethod
    def create_table_users():
        cursor = self.connection.cursor()
    '''

    # TODO: add a champion boolean to this
    def create_table_users(self, connection):
        cursor = connection.cursor()
        # TODO: Fix this to avoid injection attacks
        cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
        id integer PRIMARY KEY,
        name text NOT NULL UNIQUE,
        score integer NOT NULL DEFAULT 0 CHECK (score >= -10000),
        champion boolean DEFAULT 0
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
        INSERT OR IGNORE INTO USERS(name) VALUES(?)
        ''',
        (user,)
        )
        # save changes to db
        self.connection.commit()

    # tells us what the given user's score is
    def return_score(self, connection, user):
        cursor = connection.cursor()
        select_score_results = cursor.execute(
        '''
        SELECT SCORE FROM USERS WHERE NAME = ?
        ''',
        (user,)
        ).fetchall()
        '''
        fetchall results look like this: [(0,)],
        so we need to drill into this data structure
        '''
        # TODO: make this more elegant
        if select_score_results:
            return select_score_results[0][0]

    # gets top ten scorers from database
    def return_top_ten(self, connection):
        cursor = connection.cursor()
        top_ten = cursor.execute(
        '''
        SELECT * FROM USERS ORDER BY SCORE DESC LIMIT 10
        ''',
        ).fetchall()
        return top_ten

    # gets champion (highest scorer) from database
    def get_champion(self, connection):
        cursor = connection.cursor()
        champion_search = cursor.execute(
        '''
        SELECT NAME, MAX(SCORE) FROM USERS
        '''
        ).fetchall()
        return champion_search[0][0], '$' + str(champion_search[0][1])

    # sets champion before nightly reset
    def set_champion(self, connection, user):
        cursor = connection.cursor()
        cursor.execute(
        '''
        UPDATE USERS SET CHAMPION = 1 WHERE NAME = ?
        ''',
        (user,)
        )
        self.connection.commit()


    '''
    updates the score of a given user
    :param score_change: the amount by which we will change the user's score
    '''
    def update_score(self, connection, user, score_change):
        # UPDATE USERS SET SCORE = SCORE + ? WHERE NAME = ?
        cursor = connection.cursor()
        cursor.execute(
        '''
        UPDATE USERS
        SET SCORE = CASE
        WHEN (SCORE + ?) >= -10000 THEN (SCORE + ?)
        ELSE SCORE
        END
        WHERE NAME = ?
        ''', (score_change, score_change, user)
        )
        self.connection.commit()

    # resets scores to 0 for all users, used for nightly resets
    def wipe_scores(self, connection):
        cursor = connection.cursor()
        cursor.execute(
        '''
        UPDATE USERS SET SCORE = 0
        '''
        )
        self.connection.commit()
