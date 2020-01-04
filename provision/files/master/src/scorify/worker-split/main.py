import wave
import hashlib
import math

from utils import redis, filepath
from utils.job import Job


def GetSegments(sampleFrequency, sampleCount):
    """ Returns the list of [startPosition, length] that will correspond to the
        splitting of the raw data in segments.
    """

    # We want to sample the signal at 20Hz, therefore
    #     > fftSampleFrenquency = 20Hz
    #     > fftSampleFrenquency must divide sampleFrequency
    # which is not guartanteed. Therefore, fft points should be taken at time positions
    #     > t_n = n / fftSampleFrenquency
    # while the reals signal time points are
    #     > tp_m = m / sampleFrequency
    # We want to map n > t_n > tp_m > m such that
    #     > tp_(m-1) < t_n <= tp_m
    # which leads to
    #     m = ceil(n * sampleFrequency * fftSampleFrenquency)

    fftBatchSize = 500                                                   # Number of FFT samples to take per segment
    fftSampleLength = 1 * sampleFrequency                                   # Length of the FFT samples
    fftSampleFrenquency = 20                                                    # Frequency of the FFT sampling

    segments = []

    index = 0
    while math.ceil(index * sampleFrequency / fftSampleFrenquency) < sampleCount:
        segments.append([index, index + fftBatchSize - 1])
        index = index + fftBatchSize

    def toSamplePosition(indexes):
        return [max(math.ceil(indexes[0] * sampleFrequency / fftSampleFrenquency), 0),
                min(math.ceil(indexes[1] * sampleFrequency / fftSampleFrenquency) + fftSampleLength, sampleCount)]

    segments = list(map(toSamplePosition, segments))

    def toSegmentLength(bounds):
        return [bounds[0], bounds[1] - bounds[0]]

    segments = list(map(toSegmentLength, segments))

    if len(segments) > 1 and segments[1][1] < math.ceil(10 * sampleFrequency / fftSampleFrenquency):
        lastSegment = segments.pop()
        segments[1][1] = segments[1][1] + lastSegment[1]

    return segments


def SplitFile(job):
    """ Splits the input file in segments, and store their hash in the DB
        > rawFileHash: hash of the raw file we are working on

        Returns: True once completed
        Notify: yes
    """
    rawFileHash = job.get('hash')

    print('[split] Opening ', filepath.GetRawFromHash(rawFileHash))

    with wave.open(filepath.GetRawFromHash(rawFileHash), 'rb') as content:
        segments = GetSegments(content.getframerate(), content.getnframes())

        print('[split] File should be split in', len(segments), 'segments')

        segmentDone = 0
        segmentCount = len(segments)

        job.start(segmentCount)

        for segmentInfo in segments:
            start, length = segmentInfo[0], segmentInfo[1]
            content.setpos(start)

            data = content.readframes(length)
            hash = hashlib.md5(data).hexdigest()

            name = filepath.GetSegmentFromHash(rawFileHash, hash)
            filepath.EnsureExists(name)

            print('[split] Spliting... ', segmentDone, '/', len(segments), 'done.')

            with wave.open(name, 'wb') as segment:
                segment.setparams(content.getparams())
                segment.setnframes(length)
                segment.writeframes(data)

            data = {}
            data['segment-hash'] = hash
            data['segment-index'] = segmentDone

            redis.open().publish('JOB-UPDATE-SPLIT', job.notify(data).serialize())

            segmentDone = segmentDone + 1

            job.update(segmentDone)

        print('[split] Spliting... ', segmentDone, '/', len(segments), 'done.')

        job.complete()
        redis.open().publish('JOB-UPDATE-SPLIT', job.serialize())

        print('[split] [SUCCESS] Job', rawFileHash, flush=True)


def Dispatcher(message):
    print('[split] Dispatching message:', message['channel'], message['data'])

    if message['channel'] == b'JOB-QUEUE-UPDATE-SPLIT':
        ProcessQueue()
    elif message['channel'] == b'WORKER-STOP':
        Stop()
    else:
        print('[worker-split]: Recieved a message that was not handled', message['channel'], message['data'])


redisSubscribe = None
redisSubscribeThread = None


def ProcessQueue():
    while True:
        serializedJob = redis.open().lpop('JOB-QUEUE-SPLIT')

        if serializedJob:
            print('[split] Recieved job:', serializedJob.decode('UTF-8'), flush=True)
            SplitFile(Job.fromSerialized(serializedJob.decode('UTF-8')))
        else:
            break


def Stop():
    global redisSubscribe, redisSubscribeThread

    redisSubscribeThread.stop()
    redisSubscribe.close()


if __name__ == '__main__':
    print('[split] Starting...')
    redisSubscribe = redis.open().pubsub()
    redisSubscribe.subscribe(**{'JOB-QUEUE-UPDATE-SPLIT': Dispatcher})
    redisSubscribe.subscribe(**{'WORKER-STOP': Dispatcher})
    redisSubscribeThread = redisSubscribe.run_in_thread(sleep_time=0.5)
    print('[split] Suscribed to redis.')

    print('[split] Processing any jobs already in the queue.')
    ProcessQueue()

    print('[split] Waiting on jobs...')
