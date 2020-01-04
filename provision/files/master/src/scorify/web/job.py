from utils.redis import RedisModelBase
from utils.job import Job
from utils.constant import JOB_STATUS, REDIS_QUEUE_JOB, REDIS_PUBLISH_JOB, REDIS_PUBLISH_UPDATE


class RedisModel(RedisModelBase):
    # Init #####################################################################
    def __init__(self):
        super(RedisModel, self).__init__()
        self._message_handlers = {
            REDIS_PUBLISH_UPDATE.SPLIT: self.__onMessage_jobUpdateSplit,
            REDIS_PUBLISH_UPDATE.FFT: self.__onMessage_jobUpdateFft,
            REDIS_PUBLISH_UPDATE.PEAK: self.__onMessage_jobUpdatePeak,
            'WORKER-STOP': self.__onMessage_workerStop
        }

        self._debugHeader = '[redis-web]'

    # Overriden methods ########################################################
    def dispatch(self, message):
        channel = message['channel'].decode('UTF-8')
        job = Job.fromSerialized(message['data'].decode('UTF-8'))

        self._message_handlers.get(channel, self.__onMessage_doNothing)(job)

    # Private methods ##########################################################
    def __onMessage_doNothing(self, message):
        pass

    def __onMessage_jobUpdateSplit(self, job):
        if job.status() == JOB_STATUS.STARTED:
            # Do nothing
            pass

        if job.status() == JOB_STATUS.NOTIFY:
            newJob = Job.new(job.get('hash'), 'fft', job.data['segment-index'])
            newJob.data['segment-hash'] = job.data['segment-hash']
            newJob.data['segment-index'] = job.data['segment-index']

            self.rpush(REDIS_QUEUE_JOB.FFT, newJob.serialize())
            self.publish(REDIS_PUBLISH_JOB.FFT, '')

        if job.status() == JOB_STATUS.COMPLETED:
            pass

    def __onMessage_jobUpdateFft(self, job):
        if job.status() == JOB_STATUS.STARTED:
            # Do nothing
            pass

        if job.status() == JOB_STATUS.NOTIFY:
            # Do nothing
            pass

        if job.status() == JOB_STATUS.COMPLETED:
            newJob = Job.new(job.get('hash'), 'peak', job.data['segment-index'])
            newJob.data['segment-hash'] = job.data['segment-hash']
            newJob.data['segment-index'] = job.data['segment-index']
            newJob.data['fft-hash'] = job.data['fft-hash']

            self.rpush(REDIS_QUEUE_JOB.PEAK, newJob.serialize())
            self.publish(REDIS_PUBLISH_JOB.PEAK, '')

    def __onMessage_jobUpdatePeak(self, job):
        if job.status() == JOB_STATUS.STARTED:
            # Do nothing
            pass

        if job.status() == JOB_STATUS.NOTIFY:
            # Do nothing
            pass

        if job.status() == JOB_STATUS.COMPLETED:
            # Check if all split/fft/peak jobs are completed
            #   > if yes create a new job 'score'
            pass

    def __onMessage_workerStop(self, job):
        if job.data['worker-name'] == 'web':
            self.stop()
