import os

from tempfile import NamedTemporaryFile
import wave
import hashlib
import math
import numpy as np
from scipy.io.wavfile import read as read
import scipy.fftpack as spfft
from random import randint

import matplotlib.pyplot as plt

from utils import redis, db, filepath

def FFT(rawFileHash, segmentHash):

    # Read and convert to complex
    sampleFrequency, rdata  = read(filepath.GetSegmentFromHash(rawFileHash, segmentHash))
    data                    = rdata.astype(np.complex_)

    fftSampleFrenquency         = 80
    # fftSampleLength             = 1 * sampleFrequency
    fftSampleLength             = math.ceil(0.25 * sampleFrequency)
    hamming                     = np.reshape(np.repeat(np.hamming(fftSampleLength), data.shape[1]), (fftSampleLength, 2))

    # WAV: The number of channel is contained in the shape of data (len, numChannels)

    # We don't have the file hash yet
    file = NamedTemporaryFile(mode='w+b', dir='/data/temp', delete=False)
    # File header, [number of FFT Samples, FFT sample length, original file sample frequency, FFT sample frequency]
    file.write(np.zeros(4, dtype=np.int32).tobytes())

    total = math.floor((len(data) - fftSampleLength) * fftSampleFrenquency / sampleFrequency)

    print('[fft] Data shape:', data.shape)
    redis.open().publish('JOB-UPDATE-FFT', rawFileHash + '-' + segmentHash + '-STARTED-' + str(total))

    allData = np.array([], dtype=np.float_)

    index, nextNotification = 0, 0
    while math.ceil(index * sampleFrequency / fftSampleFrenquency) + fftSampleLength <= len(data):
        if index >= nextNotification:
            print('[fft] Processing index', index)
            nextNotification = nextNotification + randint(18, 28)
            redis.open().publish('JOB-UPDATE-FFT', rawFileHash + '-' + segmentHash + '-UPDATE-' + str(index) + '-' + str(total))

        s = math.ceil(index * sampleFrequency / fftSampleFrenquency)
        e = math.ceil(index * sampleFrequency / fftSampleFrenquency) + fftSampleLength

        fftData         = spfft.fft(data[s:e] * hamming)
        fftPowerData    = np.sum(np.absolute(fftData, dtype=np.float_), axis=1)
        fftPowerData    = 1.0 / fftSampleLength * fftPowerData ** 2

        # TODO: We could ignore the later half of the data (negative frequencies) as it's symmetric for FFT of real signals
        file.write(fftPowerData.tobytes())
        print(file.tell(), np.amax(fftPowerData))

        allData = np.append(allData, fftPowerData)

        index = index + 1

    # Should not be here
    plt.imshow(np.reshape(allData, (fftSampleLength, -1)), aspect='auto')
    filepath.EnsureExists(filepath.GetFFTFromHash(rawFileHash, segmentHash) + '.svg')
    plt.savefig(filepath.GetFFTFromHash(rawFileHash, segmentHash) + '.svg')
    # END

    file.seek(0)
    file.write(np.array([index, fftSampleLength, sampleFrequency, fftSampleFrenquency], dtype=np.int32).tobytes())

    file.close()

    print('[fft] Processing complete')
    redis.open().publish('JOB-UPDATE-FFT', rawFileHash + '-' + segmentHash + '-UPDATE-' + str(total) + '-' + str(total))
    print('[fft] Finalizing job')

    # Rename the temporary file
    fftHash  = filepath.Hash(file.name)
    filename = filepath.GetFFTFromHash(rawFileHash, fftHash)

    filepath.EnsureExists(filename)
    os.rename(file.name, filename)

    redis.open().publish('JOB-UPDATE-FFT', rawFileHash + '-' + segmentHash + '-SUCCESS-' + fftHash)
    print('[fft] [SUCCESS] Job', rawFileHash, '-', segmentHash)
    print('[fft] [SUCCESS] Job result', rawFileHash, '-', fftHash)

    return


def Parse(job):
    tokens = job.split('-')
    rawFileHash, segmentHash = tokens[0], tokens[1]

    if len(tokens) != 2:
        print('[fft] Recieved invalid job:', job)

    return tokens[0], tokens[1]


def Dispatcher(message):
    print('[fft] Dispatching message:', message['channel'], message['data'])

    if message['channel'] == b'JOB-QUEUE-UPDATE-FFT':
        ProcessQueue()
    elif message['channel'] == b'WORKER-STOP':
        Stop()
    else:
        print('[fft]: Recieved a message that was not handled', message['channel'], message['data'])


def ProcessQueue():
    while True:
        job = redis.open().lpop('JOB-QUEUE-FFT')

        if job:
            print('[fft] Recieved job:', job.decode('UTF-8'))
            rawFileHash, segmentHash = Parse(job.decode('UTF-8'))
            FFT(rawFileHash, segmentHash)
        else:
            break


redisSubscribe          = None
redisSubscribeThread    = None

def Stop():
    global redisSubscribe, redisSubscribeThread

    redisSubscribeThread.stop()
    redisSubscribe.close()


if __name__ == '__main__':
    print('[fft] Starting...')
    redisSubscribe = redis.open().pubsub()
    redisSubscribe.subscribe(**{'JOB-QUEUE-UPDATE-FFT': Dispatcher})
    redisSubscribe.subscribe(**{'WORKER-STOP': Dispatcher})
    redisSubscribeThread = redisSubscribe.run_in_thread(sleep_time=0.5)
    print('[fft] Suscribed to redis.')

    print('[fft] Processing any jobs already in the queue.')
    ProcessQueue()

    print('[fft] Waiting on jobs...')
