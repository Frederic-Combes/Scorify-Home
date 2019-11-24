import os

from tempfile import NamedTemporaryFile

import math
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from random import randint

from utils import redis, db, filepath

def Score(hash):
    print('[score] Starting job...')
    redis.open().publish('JOB-UPDATE-SCORE', hash + '-STARTED-' + str(1))

    directory = filepath.GetDirectoryFromHash(hash, 'peak')

    filepaths = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    peaks = np.empty(0, dtype=np.float_)

    for peakHash in filepaths:
        with open(filepath.GetPeakFromHash(hash, peakHash), 'rb') as content:
            headerData  = np.frombuffer(content.read(4*4), dtype=np.int32)
            print('[score] Header data:', headerData)
            data        = np.frombuffer(content.read(), dtype=np.float_)
            peaks       = np.append(peaks, data)

    average = np.average(peaks)
    print('[score] Average is:', average)
    peaks = peaks.reshape(-1, 88)
    print('[score] Final shape is:', peaks.shape)

    figure, axes = plt.subplots()

    axes.set_title('Score of ' + hash)
    axes.set_xlabel('time index (at 20Hz)')
    axes.set_ylabel('key')

    # Guitar: low E is key #20, while high E is key #44
    plt.imshow(peaks.T, origin='lower', aspect='auto')

    figureFilepath = os.path.join(filepath.GetDirectoryFromHash(hash, 'fig'), 'score.svg')
    filepath.EnsureExists(figureFilepath)
    figure.savefig(figureFilepath)

    return


def Parse(job):
    tokens = job.split('-')
    rawFileHash = tokens[0]

    if len(tokens) != 1:
        print('[score] Recieved invalid job:', job)

    return tokens[0]


def Dispatcher(message):
    if message['channel'] == b'JOB-QUEUE-UPDATE-SCORE':
        ProcessQueue()
    elif message['channel'] == b'WORKER-STOP':
        Stop()
    else:
        print('[score] Message was not handled:', message['channel'], message['data'])


def ProcessQueue():
    while True:
        job = redis.open().lpop('JOB-QUEUE-SCORE')

        if job:
            print('[score] Recieved job:', job.decode('UTF-8'))
            hash = Parse(job.decode('UTF-8'))
            Score(hash)
        else:
            break


redisSubscribe          = None
redisSubscribeThread    = None

def Stop():
    global redisSubscribe, redisSubscribeThread

    redisSubscribeThread.stop()
    redisSubscribe.close()


if __name__ == '__main__':
    print('[score] Starting...')

    print('[score] Processing any jobs already in the queue.')
    ProcessQueue()

    print('[score] Suscribing to redis.')
    redisSubscribe = redis.open().pubsub()
    redisSubscribe.subscribe(**{'JOB-QUEUE-UPDATE-SCORE': Dispatcher})
    redisSubscribe.subscribe(**{'WORKER-STOP': Dispatcher})
    redisSubscribeThread = redisSubscribe.run_in_thread(sleep_time=0.5)

    print('[score] Waiting on jobs...')
