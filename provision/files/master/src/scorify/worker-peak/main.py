import os

from tempfile import NamedTemporaryFile
import numpy as np

import matplotlib.pyplot as plt

from utils import redis, filepath
from utils.job import Job


def NoteBins(n, f):
    # Source : https://en.wikipedia.org/wiki/Piano_key_frequencies
    # return [[math.floor(math.pow(2.0, (i-0.5-49) / 12) * 440.0 * n / f), math.ceil(math.pow(2.0, (i+0.5-49) / 12) * 440.0 * n / f)] for i in range(1, 89)]
    return [[0 + 10*i, 10 + 10*i] for i in range(1, 89)]


def Peak(job):
    rawFileHash = job.get('hash')
    fftHash = job.data['fft-hash']

    with open(filepath.GetFFTFromHash(rawFileHash, fftHash), 'rb') as content:
        headerData = np.frombuffer(content.read(4*4), dtype=np.int32)

        indexCount, fftSampleLength, sampleFrequency, fftSampleFrenquency = headerData[0], headerData[1], headerData[2], headerData[3]

        job.start(indexCount.item())
        print('[peak] Header data:', indexCount, fftSampleLength, sampleFrequency, fftSampleFrenquency)

        noteBins = NoteBins(sampleFrequency, fftSampleLength)
        allPeaks = np.array([], dtype=np.float_)

        for i in range(indexCount):
            # We only consider the highest peak for each note
            data = np.frombuffer(content.read(fftSampleLength * 8), dtype=np.float_)
            # print(content.tell(), np.amax(data))
            allPeaks = np.append(allPeaks, np.array([np.amax(data[noteBin[0]:noteBin[1]]) for noteBin in noteBins], dtype=np.float_))

            job.update(i)

        print('[peak] Processing complete. Shape:', allPeaks.shape)
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

        job.data['peak-hash'] = peakHash
        job.complete()
        redis.open().publish('JOB-UPDATE-PEAK', job.serialize())

        print('[peak] [SUCCESS] Job', rawFileHash, '-', fftHash)
        print('[peak] [SUCCESS] Job result', rawFileHash, '-', peakHash)

    return


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
        serializedJob = redis.open().lpop('JOB-QUEUE-PEAK')

        if serializedJob:
            print('[peak] Recieved job:', serializedJob.decode('UTF-8'), flush=True)
            Peak(Job.fromSerialized(serializedJob.decode('UTF-8')))
        else:
            break


redisSubscribe = None
redisSubscribeThread = None


def Stop():
    global redisSubscribe, redisSubscribeThread

    redisSubscribeThread.stop()
    redisSubscribe.close()


if __name__ == '__main__':
    print('[peak] Starting...')
    redisSubscribe = redis.open().pubsub()
    redisSubscribe.subscribe(**{'JOB-QUEUE-UPDATE-PEAK': Dispatcher})
    redisSubscribe.subscribe(**{'WORKER-STOP': Dispatcher})
    redisSubscribeThread = redisSubscribe.run_in_thread(sleep_time=0.5)
    print('[peak] Suscribed to redis.')

    print('[peak] Processing any jobs already in the queue.')
    ProcessQueue()

    print('[peak] Waiting on jobs...')
