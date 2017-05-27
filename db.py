import sqlite3

'''
Class for database setup/functions
This will primarily serve to store users and track their scores/money totals
'''

class db(object):

    def __init__(self, db_file):
        self.db_file = "database_files/" + db_file
        self.connection = self.create_connection(self.db_file)
        self.create_table(self.connection)

    def create_connection(self, db_file):
        return sqlite3.connect(db_file)

    '''
    :param connection: connection to the sql database
    :sql_param name: name of user
    :sql_param score: current money value of user
    '''
    def create_table(self, connection):
        cursor = connection.cursor()
        cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users(
        id integer PRIMARY KEY,
        name text NOT NULL UNIQUE,
        score integer NOT NULL DEFAULT 0
        );
        '''
        )

    # add user if they don't already exist in the database
    def add_user_to_db(self, connection, user):
        cursor = connection.cursor()
        cursor.execute(
        '''
        INSERT INTO USERS(name) VALUES(?)
        ''',
        (user,)
        )
        # save changes to db
        self.connection.commit()
