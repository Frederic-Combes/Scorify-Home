import mysql.connector as sql
import os

_DATABASE_CONFIGURATION = {
    'host': os.environ.get('DATABASE_HOST', 'mariadb'),
    'port': os.environ.get('DATABASE_PORT', '3306'),
    'user': os.environ.get('DATABASE_USER', 'scorify'),
    'passwd': os.environ.get('DATABASE_USER_PASSWORD', 'password@scorify'),
    'db': os.environ.get('DATABASE_NAME', 'scorify')
}

_DATABASE_ROOT_CONFIGURATION = {
    'host': os.environ.get('DATABASE_HOST', 'mariadb'),
    'port': os.environ.get('DATABASE_PORT', '3306'),
    'user': 'root',
    'passwd': os.environ.get('DATABASE_ROOT_PASSWORD', 'password@root'),
    'db': os.environ.get('DATABASE_NAME', 'scorify')
}


class MySQLDatabaseCursor:
    def __init__(self, commit=True, configuration=_DATABASE_CONFIGURATION, buffered=False):
        self._commit = commit
        self._buffered = buffered
        self._configuration = configuration

    def __enter__(self):
        self._connection = sql.connect(**self._configuration)
        self._cursor = self._connection.cursor(buffered=self._buffered)
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._commit:
            self._connection.commit()

        self._cursor.close()
        self._connection.close()
        return


def ensureInitialized():
    print('[db] Ensuring the database is initialized...')

    sqlDirectory = os.path.join(os.path.dirname(__file__), 'sql', 'ensure_initialized')

    databaseName = os.environ.get('DATABASE_NAME', 'scorify')

    with MySQLDatabaseCursor(configuration=_DATABASE_CONFIGURATION, buffered=True) as cursor:
        print('[db] Successfully connected to the database.')

        # Table job_info
        with open(os.path.join(sqlDirectory, 'if_table_exists.sql'), 'r') as file:
            query = file.read()
        cursor.execute(query.format(databaseName, 'job_info'))

        if len(cursor.fetchall()) == 0:
            print('[db] Table job_info absent. Creating ...')
            with open(os.path.join(sqlDirectory, 'create_table_job_info.sql'), 'r') as file:
                query = file.read()
            cursor.execute(query)
            print('[db] Ran query:', cursor.query)
        else:
            print('[db] Table job_info already present. Nothing to do.')

        # Table job_status
        with open(os.path.join(sqlDirectory, 'if_table_exists.sql'), 'r') as file:
            query = file.read()
        cursor.execute(query.format(databaseName, 'job_status'))

        if len(cursor.fetchall()) == 0:
            print('[db] Table job_status absent. Creating...')
            with open(os.path.join(sqlDirectory, 'create_table_job_status.sql'), 'r') as file:
                query = file.read()
            cursor.execute(query)
            print('[db] Ran query:', cursor.query)
        else:
            print('[db] Table job_status already present. Nothing to do.')

    # TODO: Check that the table follows the right schema

    print('[db] Done.')
