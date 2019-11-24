import mysql.connector as sql

dbConfig = {
    'user' : 'scorify',
    'host' : '#',
    'user' : 'scorify',
    'passwd' : '#',
    'db' : 'scorify',
}

connection, isConnected = None, False

def open():
    ''' Ensures a connection to the DB is open and returns a cursor to excecute
        queries
    '''
    global connection, isConnected

    if isConnected:
        return connection.cursor()
    else:
        try:
            connection = sql.connect(**dbConfig)
            isConnected = True
            return connection, connection.cursor()
        except:
            print("Failed to open DB connection")

def close():
    ''' Closes the DB connection '''
    global connection, isConnected

    try:
        connection.close()
        isConnected = False
    except:
        print("Failed to close DB connection")

def InitDB():
    ''' Ensures the database follows the correct schema '''
    connection, cursor = OpenDB()
    cursor.execute("DROP TABLE segments;")
    cursor.excecute("CREATE TABLE segments (rawFileHash VARCHAR(64), segmentHash VARCHAR(64), start INT, lenght INT)")
    # cursor.excecute("CREATE TABLE fft (rawFileHash VARCHAR(64), segmentHash VARCHAR(64), fftHash VARCHAR(64))")
    connection.commit()
    return
