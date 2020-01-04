from threading import Thread, Lock

import time
import os
import redis

redisConnection, redisIsConnected = None, False


def open():
    global redisConnection, redisIsConnected

    if redisIsConnected:
        return redisConnection
    else:
        try:
            redisConfig = {}

            redisConfig['host'] = os.environ.get('REDIS_HOST', 'redis')
            redisConfig['port'] = os.environ.get('REDIS_PORT', '6379')
            redisConfig['db'] = 0

            redisConnection = redis.Redis(**redisConfig)
            redisIsConnected = True
            return redisConnection
        except redis.ConnectionError:
            print("Failed to connect to Redis")


def close():
    return


class RedisModelBase():
    # Init #####################################################################
    def __init__(self):
        self._connection = self.__getConnection()
        self._pubsub = self._connection.pubsub(ignore_subscribe_messages=True)

        self._queues = {
            'publish': {'queue': [], 'func': lambda r, c, m: r.publish(c, m)},
            'rpush': {'queue': [], 'func': lambda r, c, m: r.rpush(c, m)}
        }

        self._failedConnections = 0
        self._breakLoop = False
        self._thread = Thread(target=self.__mainLoop)
        self._lock = Lock()

        self._debugHeader = '[redis model base]'

    # Mehtods that must be overridden ##########################################
    def dispatch(self):
        """ Method to override when inheriting """
        pass

    # Public methods ###########################################################
    def start(self, *channels):
        """ Register channels to subscribe to and starts the main loop in a thread """
        self._pubsub.subscribe(channels)

        self._thread.start()

    def stop(self):
        """ Stops the main loop and unregister all subscribed channels """
        with self._lock:
            self._breakLoop = True

        self._thread.join()
        self._pubsub.unsuscribe()

    def publish(self, channel, message):
        """ Queues a PUBLISH message """
        self.__queue('publish', channel, message)

    def rpush(self, channel, message):
        """ Queues a RPUSH message """
        self.__queue('rpush', channel, message)

    # Private methods start here ###############################################
    def __mainLoop(self):
        """ Main thread loop """
        while True:
            with self._lock:
                if self._breakLoop:
                    break

            self.__dispatchMessages()
            self.__processQueues()

            time.sleep(0.1)

    def __getConnection(self):
        """ Returns a connection to redis """
        config = {
            'host': os.environ.get('REDIS_HOST', 'redis'),
            'port': os.environ.get('REDIS_PORT', '6379'),
            'db': os.environ.get('REDIS_DB', '0')
        }

        return redis.Redis(**config)

    def __waitBeforeReconnecting(self):
        """ In case the last connection to Redis failed, imposes a waiting time """
        if self._failedConnections == 0:
            return
        elif self._failedConnections > 3:
            print(self._debugHeader, 'Attempting to connect again in a minute...', flush=True)
            time.sleep(60)
        else:
            print(self._debugHeader, 'Attempting again in 5 seconds...', flush=True)
            time.sleep(5)

    def __dispatchMessages(self):
        """ Dispatches messages current hold in Redis """
        try:
            message = self._pubsub.get_message()
        except redis.ConnectionError:
            print(self._debugHeader, 'unexpected ConnectionError occured.', flush=True)
            self._failedConnections = self._failedConnections + 1
        except redis.RedisError as err:
            print(self._debugHeader, 'unexpected RedisError occured.', flush=True)
            raise err
        else:
            self._failedConnections = 0

        if message:
            self.__dispatch(message)

        self.__waitBeforeReconnecting()

    def __dispatch(self, message):
        self.dispatch(message)

    def __queue(self, queue, channel, message):
        """ Private handler for queueing """
        with self._lock:
            self._queues[queue]['queue'].append({'channel': channel, 'message': message})

    def __processQueues(self):
        """ Sends all queued messages to Redis """
        for queue in ['rpush', 'publish']:
            while True:
                with self._lock:
                    if len(self._queues[queue]['queue']) == 0:
                        break

                    message = self._queues[queue]['queue'][0]

                    try:
                        self._queues[queue]['func'](self._connection, message['channel'], message['message'])
                    except redis.ConnectionError:
                        print(self._debugHeader, 'unexpected ConnectionError occured.', flush=True)
                        self._failedConnections = self._failedConnections + 1
                        break
                    else:
                        self._failedConnections = 0

                    self._queues[queue]['queue'].pop(0)

        self.__waitBeforeReconnecting()
