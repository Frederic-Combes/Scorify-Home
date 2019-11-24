import os

from tempfile import NamedTemporaryFile
import wave
import hashlib
import math
import numpy as np

from scipy.signal import find_peaks
from random import randint

import matplotlib.pyplot as plt

from utils import redis, db, filepath

def NoteBins(n, f):
    # Source : https://en.wikipedia.org/wiki/Piano_key_frequencies
    # return [[math.floor(math.pow(2.0, (i-0.5-49) / 12) * 440.0 * n / f), math.ceil(math.pow(2.0, (i+0.5-49) / 12) * 440.0 * n / f)] for i in range(1, 89)]
    return [[0 + 10*i, 10 + 10*i] for i in range(1, 89)]

def Peak(rawFileHash, fftHash):
    with open(filepath.GetFFTFromHash(rawFileHash, fftHash), 'rb') as content:
        headerData = np.frombuffer(content.read(4*4), dtype=np.int32)

        indexCount, fftSampleLength, sampleFrequency, fftSampleFrenquency = headerData[0], headerData[1], headerData[2], headerData[3]

        print('[peak] Header data:', indexCount, fftSampleLength, sampleFrequency, fftSampleFrenquency)
        redis.open().publish('JOB-UPDATE-PEAK', rawFileHash + '-' + fftHash + '-STARTED-' + str(indexCount))

        noteBins = NoteBins(sampleFrequency, fftSampleLength)
        allPeaks = np.array([], dtype=np.float_)

        nextNotification = 0
        for i in range(indexCount):
            # We only consider the highest peak for each note
            data = np.frombuffer(content.read(fftSampleLength * 8), dtype=np.float_)
            print(content.tell(), np.amax(data))
            allPeaks = np.append(allPeaks, np.array([np.amax(data[noteBin[0]:noteBin[1]]) for noteBin in noteBins], dtype=np.float_))

            if i >= nextNotification:
                print('[peak] Processing index', i)
                nextNotification = nextNotification + randint(18, 28)
                redis.open().publish('JOB-UPDATE-PEAK', rawFileHash + '-' + fftHash + '-UPDATE-' + str(i) + '-' + str(indexCount))

        print('[peak] Processing complete. Shape:', allPeaks.shape)
        redis.open().publish('JOB-UPDATE-PEAK', rawFileHash + '-' + fftHash + '-UPDATE-' + str(indexCount) + '-' + str(indexCount))
        print('[peak] Finalizing job')

        tmpFile = NamedTemporaryFile(mode='w+b', dir='/data/temp', delete=False)
        tmpFile.write(headerData.tobytes())
        tmpFile.write(allPeaks.tobytes())

        tmpFile.close()

        # Rename the temporary file
        peakHash = filepath.Hash(tmpFile.name)
        filename = filepath.GetPeakFromHash(rawFileHash, peakHash)

        filepath.EnsureExists(filename)
        os.rename(tmpFile.name, filename)

        # Should not be here
        plt.imshow(np.reshape(allPeaks, (-1, 88)), aspect='auto')
        filepath.EnsureExists(os.path.join(filepath.GetDirectoryFromHash(rawFileHash, 'fig'), 'raw.svg'))
        plt.savefig(os.path.join(filepath.GetDirectoryFromHash(rawFileHash, 'fig'), 'raw.svg'))
        # END

        redis.open().publish('JOB-UPDATE-PEAK', rawFileHash + '-' + fftHash + '-SUCCESS-' + peakHash)
        print('[peak] [SUCCESS] Job', rawFileHash, '-', fftHash)
        print('[peak] [SUCCESS] Job result', rawFileHash, '-', fftHash)

    return


def Parse(job):
    tokens = job.split('-')
    rawFileHash, fftHash = tokens[0], tokens[1]

    if len(tokens) != 2:
        print('[peak] Recieved invalid job:', job)

    return tokens[0], tokens[1]


def Dispatcher(message):
    print('[peak] Dispatching message:', message['channel'], message['data'])

    if message['channel'] == b'JOB-QUEUE-UPDATE-PEAK':
        ProcessQueue()
    elif message['channel'] == b'WORKER-STOP':
        Stop()
    else:
        print('[peak]: Recieved a message that was not handled', message['channel'], message['data'])


def ProcessQueue():
    while True:
        job = redis.open().lpop('JOB-QUEUE-PEAK')

        if job:
            print('[peak] Recieved job:', job.decode('UTF-8'))
            rawFileHash, segmentHash = Parse(job.decode('UTF-8'))
            Peak(rawFileHash, segmentHash)
        else:
            break


redisSubscribe          = None
redisSubscribeThread    = None

def Stop():
    global redisSubscribe, redisSubscribeThread

    redisSubscribeThread.stop()
    redisSubscribe.close()


if __name__ == '__main__':
    print('[peak] Starting...')

    print('[peak] Processing any jobs already in the queue.')
    ProcessQueue()

    print('[peak] Suscribing to redis.')
    redisSubscribe = redis.open().pubsub()
    redisSubscribe.subscribe(**{'JOB-QUEUE-UPDATE-PEAK': Dispatcher})
    redisSubscribe.subscribe(**{'WORKER-STOP': Dispatcher})
    redisSubscribeThread = redisSubscribe.run_in_thread(sleep_time=0.5)

    print('[peak] Waiting on jobs...')
