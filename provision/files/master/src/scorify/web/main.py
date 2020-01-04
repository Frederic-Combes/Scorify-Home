""" Scorify WebApp : main """
import os

# TODO: Turn all line endings to LF (linux) (REQUIRES FIBER OPTICS CONNECTION)

# Libs/Modules
#   > NFS Server: https://hub.docker.com/r/erichough/nfs-server
#   > Redis: Channels :
#       > JOB-QUEUE-UPDATE-* : web publishes a message when there are new jobs for the channel JOB-QUEUE-*
#       > JOB-UPDATE-*: Workers publish here when they report progress
#       > JOB-QUEUE-*: Queue for job *
#
# ###> Python bindings for NFS Client: https://pypi.org/project/pyNfsClient/

# Use a NFS Client? Maybe start a NFS Server via Docker/Kubernetes and then
# mount the NFS in the containers via Kubernetes?
# ? https://github.com/kubernetes-incubator/external-storage/tree/master/nfs-client
# Example: ? https://medium.com/platformer-blog/nfs-persistent-volumes-with-kubernetes-a-case-study-ce1ed6e2c266

# Kubernests & Work Queue:
# ? https://kubernetes.io/docs/tasks/job/fine-parallel-processing-work-queue/

# Logic:
#   > Upload file from user
#       > Store on the NFS as hash(rawfile)/raw
#       > Insert the file hash in the DB as well as the file extension, ans timestamp
#       > Redirect webpage to /result/hash(rawfile)
#
#   > Process: Raw to Segments
#       > Split file into segments ; insert the hash into the DB
#       > Store the segments on the NFS in hash(rawfile)/segment/hash(segment)
#       > Updated the webpage as segment are created
#
#   > Process file: Segments to FFT
#       > Once the file has been split into segments
#       > Redis the "perform FFT" message for each segment
#       > Update webpage as segments report progress
#       > FFT result stored on the NFS as hash(rawfile)/fft/hash(fft:segment)
#       > Update the DB, mark segement FFT as processed and insert its hash
#
#   > Process file: FFT to Peaks
#       > Once a segment reports that the FFT has been performed
#       > Redis the "perform peak" for the segment
#       > Update page as workers are reporting progress for the segments
#       > Peak results are stored as hash(rawfile)/peak/hash(peak:segment)
#       > Update the DB, mark the segment Peak as processed and insert its hash
#
#   > Process file: Peak to Score
#       > Once all segments report that the Peak has been performed
#       > Redis the "merge & score" for the rawfile hash
#       > Update the webpage as the worker reports progress
#       > Redirect webpage to /result/file?=hash(rawfile)
#       > Score stored on the NFS as hash(rawfile)/result.score
#       > Update the DB, mark the file as processed
#
# Workers: 4
#   > Segment: takes a raw file (raw file hash) and splits it into segments
#   > FFT: takes a segment (segment hash)
#   > Peak: takes a segment
#   > Score: takes all peak segments

# Project Utils ##################################################################

from utils import filepath, db
from utils.db import MySQLDatabaseCursor
from utils.job import Job
from utils.constant import REDIS_PUBLISH_JOB, REDIS_QUEUE_JOB, REDIS_PUBLISH_UPDATE

from job import RedisModel

# Flask App ####################################################################

from flask import Flask
from flask import flash, request, redirect, render_template
from flask_socketio import SocketIO, emit

APP = Flask(__name__, static_url_path='', static_folder='static')
APP.secret_key = "secret key"

APP.config['UPLOAD_FOLDER'] = '/data'
APP.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
APP.config['ALLOWED_EXTENSIONS'] = set(['wav'])

# SIO = SocketIO(APP, logger=False, engineio_logger=False)
SIO = SocketIO(APP)

redisModel = RedisModel()


def isFileAllowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in APP.config['ALLOWED_EXTENSIONS']


@APP.route('/')
def home():
    """ Generates and return the site homepage """
    return render_template('upload.html.j2')


@APP.route('/', methods=['POST'])
def upload_file():
    """ Uploads the file """
    if request.method == 'POST':
        if 'file' not in request.files:                                         # Not an upload request
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':                                                 # No file selected
            flash('No file selected for uploading')
            return redirect(request.url)

        if file and isFileAllowed(file.filename):                               # File has the correct extension
            # Temporarily saving the file
            filepath.EnsureExists('/data/temp-hash/raw')
            file.save('/data/temp-hash/raw')

            hash = filepath.Hash('/data/temp-hash/raw')
            filename = filepath.GetRawFromHash(hash)

            filepath.EnsureExists(filename)

            # Moving the temporary file to it's destination
            os.rename('/data/temp-hash/raw', filename)

            print('[web] File successfully uploaded. Saved as:' + filename, flush=True)

            job = Job.new(hash, 'split')

            redisModel.rpush(REDIS_QUEUE_JOB.SPLIT, job.serialize())
            redisModel.publish(REDIS_PUBLISH_JOB.SPLIT, '')

            print('[web] Job created. File is being processed.')

            return redirect('/result/' + job.get('hash'))
        else:
            flash('Only wav files are allowed')                                 # File doesn't have the correct expansion
            return redirect(request.url)

    # Make it pretty: https://www.jitsejan.com/python-and-javascript-in-flask.html


@APP.route('/result/<string:hash>')
def resultPage(hash):
    return render_template('result.html.j2', hash=hash)


@SIO.on('connect')
def onConnect():
    return


@SIO.on('disconnect')
def onDisconnect():
    return


@SIO.on('request-update')
def onRequestUpdate(hash):
    progressData = {
        'split': {'name': 'split', 'count': 0, 'data': []},
        'fft': {'name': 'fft', 'count': 0, 'data': []},
        'peak': {'name': 'peak', 'count': 0, 'data': []},
        'score': {'name': 'score', 'count': 0, 'data': []}
    }

    with MySQLDatabaseCursor() as cursor:
        query = '''SELECT `name`, `uid`, `order` FROM job_info WHERE `hash` = '{0}' '''
        cursor.execute(query.format(hash))

        for infoRow in cursor.fetchall():
            name, uid, order = infoRow[0], infoRow[1], infoRow[2]

            query = '''SELECT `status`, `progress`, `total` FROM job_status WHERE `uid` = '{0}' '''
            cursor.execute(query.format(uid))

            statusRow = cursor.fetchone()

            if statusRow:
                status, progress, total = statusRow[0], statusRow[1], statusRow[2]

                progressData[name]['count'] = progressData[name]['count'] + 1
                progressData[name]['data'].append({
                    'order': order,
                    'status': status,
                    'progress': progress,
                    'total': total,
                })

    emit('update', progressData['split'])
    emit('update', progressData['fft'])
    emit('update', progressData['peak'])
    # emit('update', progressData['score'])


if __name__ == '__main__':
    print('[web] Checking database...')
    db.ensureInitialized()

    print('[web] Checking Redis...')
    redisModel.start(REDIS_PUBLISH_UPDATE.SPLIT, REDIS_PUBLISH_UPDATE.FFT, REDIS_PUBLISH_UPDATE.PEAK, 'WORKER-STOP')

    # import logging
    # logging.basicConfig(filename='error.log', level=logging.DEBUG)

    print('[web] Starting...')
    SIO.run(APP, host='0.0.0.0', port=5000, debug=False)
    print('[web] Awaiting requests...')
