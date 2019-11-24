import os, redis

redisConnection, redisIsConnected = None, False

def open():
    global redisConnection, redisIsConnected

    if redisIsConnected:
        return redisConnection
    else:
        try:
            redisConfig = {}

            # redisConfig['host'] = os.environ['REDIS_HOST']
            # redisConfig['port'] = os.environ['REDIS_PORT']
            redisConfig['host'] = "127.0.0.1"
            redisConfig['port'] = 6379
            redisConfig['db'] = 0

            redisConnection = redis.Redis(**redisConfig)
            redisIsConnected = True
            return redisConnection
        except:
            print("Failed to connect to Redis")


def close():
    return


def test():
    redis = open()

    redis.set('TEST-MESSAGE', 'This is a test')
    print('[redis] Test message sent:', 'This is a test')
    print('[redis] Test message recieved:', redis.get('TEST-MESSAGE'))

    return True
