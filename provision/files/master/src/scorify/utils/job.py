import uuid
from datetime import datetime
import json

from utils.db import MySQLDatabaseCursor
from utils.constant import JOB_STATUS

_TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


class Job:
    def __init__(self, **kwargs):
        if 'hash' in kwargs and 'name' in kwargs:
            self.__createNew(kwargs['hash'], kwargs['name'], kwargs['order'])
            return

        if 'serializedString' in kwargs:
            self.__createFromSerialized(kwargs['serializedString'])
            return

        raise Exception('Job object must be created from Job.new or Job.fromSerialized')

    # Private initialization methods ###########################################
    def __createNew(self, hash, name, order=0):
        self._job = {
            'hash': hash,
            'name': name,
            'uid': str(uuid.uuid4()),
            'order': order,
            'status': JOB_STATUS.CREATED,
            'creation_time': datetime.now().strftime(_TIMESTAMP_FORMAT),
            'update_time': datetime.now().strftime(_TIMESTAMP_FORMAT),
        }
        self.data = {}

        jobInfoColumns = ['hash', 'name', 'uid', 'order']
        jobInfoValues = [self._job[column] for column in jobInfoColumns]
        jobInfoPlaceholder = ', '.join(['%s'] * len(jobInfoColumns))
        jobInfoColumns = ['`' + column + '`' for column in jobInfoColumns]

        jobStatusColumns = ['uid', 'status', 'creation_time', 'update_time']
        jobStatusValues = [self._job[column] for column in jobStatusColumns]
        jobStatusPlaceholder = ', '.join(['%s'] * len(jobStatusColumns))
        jobStatusColumns = ['`' + column + '`' for column in jobStatusColumns]

        with MySQLDatabaseCursor() as cursor:
            jobInfoQuery = '''INSERT INTO job_info ({0}) VALUES ({1})'''.format(', '.join(jobInfoColumns), jobInfoPlaceholder)
            cursor.execute(jobInfoQuery, jobInfoValues)
            jobStatusQuery = '''INSERT INTO job_status ({0}) VALUES ({1})'''.format(', '.join(jobStatusColumns), jobStatusPlaceholder)
            cursor.execute(jobStatusQuery, jobStatusValues)

    def __createFromSerialized(self, serializedString):
        self._job = json.loads(serializedString)
        self.data = self._job.pop('data', {})

    # Public 'constructors' ####################################################
    @classmethod
    def new(cls, hash, name, order=0):
        """ Creates a new Job object """
        return cls(**{'hash': hash, 'name': name, 'order': order})

    @classmethod
    def fromSerialized(cls, serializedString):
        """ Builds a Job object from its serialized string """
        return cls(**{'serializedString': serializedString})

    # Public ###################################################################
    def start(self, total):
        """ Sets the jobs status to 'started' and updates the database

            - total[INT]: estimated ammount of steps needed to complete the job
        """
        with MySQLDatabaseCursor() as cursor:
            self._job['status'] = JOB_STATUS.STARTED
            self.__updateDatabaseValue_status(cursor)

            self._job['update_time'] = datetime.now().strftime(_TIMESTAMP_FORMAT)
            self.__updateDatabaseValue_update_time(cursor)

            self._job['total'] = total
            self._job['progress'] = 0
            self.__updateDatabaseValue_progress_total(cursor)

    def update(self, progress, total=None):
        """ Updates the job progress value and updates the database

            - progress[INT]: job progress, between 0 and job['total']
            - total[INT or None]: estimated amount of steps needed to complete the job
        """
        if total is None:
            total = self._job['total']

        with MySQLDatabaseCursor() as cursor:
            if self._job['status'] != JOB_STATUS.STARTED:
                self._job['status'] = JOB_STATUS.STARTED
                self.__updateDatabaseValue_status(cursor)

            self._job['update_time'] = datetime.now().strftime(_TIMESTAMP_FORMAT)
            self.__updateDatabaseValue_update_time(cursor)

            self._job['total'] = total
            self._job['progress'] = progress
            self.__updateDatabaseValue_progress_total(cursor)

    def notify(self, data=None):
        """ Creates a notify job (a copy of a job whose status cannot be changed
            and which is not insterted into the database)
        """
        return NotifyJob(self, data)

    def complete(self):
        """ Sets the status of the job to completed and updates the database
            Additionnaly sets progress = total
        """
        with MySQLDatabaseCursor() as cursor:
            self._job['status'] = JOB_STATUS.COMPLETED
            self.__updateDatabaseValue_status(cursor)

            self._job['update_time'] = datetime.now().strftime(_TIMESTAMP_FORMAT)
            self.__updateDatabaseValue_update_time(cursor)

            self._job['progress'] = self._job['total']
            self.__updateDatabaseValue_progress_total(cursor)

    def serialize(self):
        """ Serialize the object to a string """
        self._job['data'] = self.data
        serializedString = json.dumps(self._job)
        self.data = self._job.pop('data', {})
        return serializedString

    def get(self, field):
        """ Returns the value associated to the field field, or None if the
            field is not present. Guaranteed fields are:
                - uid [UID STRING], name [STRING], status [STRING],
                    creation_time [TIMESTAMP STRING], update_time [TIMESTAMP STRING],
                    (data [JSON DICT])
            Possible fields are:
                - progress [POSITIVE INT], total [POSITIVE INT]
        """
        return self._job.get(field, None)

    def status(self):
        return self._job['status']

    def data(self):
        """ Returns job-specific data, json format """
        return self._job['data']

    # Private ##################################################################
    def __updateDatabaseValue_status(self, cursor):
        query = '''UPDATE job_status SET `status` = %s WHERE `uid` = %s'''
        cursor.execute(query, [self._job['status'], self._job['uid']])

    def __updateDatabaseValue_update_time(self, cursor):
        query = '''UPDATE job_status SET `update_time` = %s WHERE `uid` = %s'''
        cursor.execute(query, [self._job['update_time'], self._job['uid']])

    def __updateDatabaseValue_progress_total(self, cursor):
        query = '''UPDATE job_status SET `total` = %s, `progress` = %s WHERE `uid` = %s'''
        cursor.execute(query, [self._job['total'], self._job['progress'], self._job['uid']])


class NotifyJob(Job):
    def __init__(self, job, data=None):
        self._job = {}
        self.data = {}

        for key, value in job._job.items():
            self._job[key] = value

        for key, value in job.data.items():
            self.data[key] = value

        if data is not None:
            for key, value in data.items():
                self.data[key] = value

        self._job['status'] = JOB_STATUS.NOTIFY

    def start(self):
        raise Exception("Notification jobs cannot be started")

    def update(self):
        raise Exception("Notification jobs cannot be updated")

    def complete(self):
        raise Exception("Notification jobs cannot be completed")
