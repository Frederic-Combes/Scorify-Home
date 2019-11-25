""" Scorify WebbApp : main """
import os

# Libs/Modules
#   > NFS Server: https://hub.docker.com/r/erichough/nfs-server
#   > Redis: Channels :
#       > JOB-QUEUE-UPDATE-* : web publishes a message when there are new jobs for the channel JOB-QUEUE-*
#       > JOB-UPDATE-*: Workers publish here when they report progress
#       > JOB-QUEUE-*: Queue for job *
#
#   > Pyhton bindings for MySQL DB: pip install mysqlclient
####> Python bindings for NFS Client: https://pypi.org/project/pyNfsClient/

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
#       > Redirect webpage to /process/file?=hash(rawfile)
#
#   > Process: Raw to Segments
#       > Split file into segments ; insert the hash into the DB
#       > Store the segments on the NFS in hash(rawfile)/segment/hash(segment)
#       > Updated the webpage as segment are created
#
#   > Process file: Segments to FFT
#       > Once the file has been split into segments
#       > RabbitMQ the "perform FFT" message for each segment
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
#   #1 > Segment: takes a raw file (raw file hash) and splits it into segments
#   > FFT: takes a segment (segment hash)
#   > Peak: takes a segment
#   > Score: takes all peak segments

# Project Utils ##################################################################

from utils import redis, db, filepath

# Flask App ####################################################################

from flask import Flask
from flask import flash, request, redirect, render_template
from flask_socketio import SocketIO, emit, send

from werkzeug.utils import secure_filename

APP = Flask(__name__, static_url_path='', static_folder='static')
APP.secret_key = "secret key"

APP.config['UPLOAD_FOLDER'] = '/data'
APP.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
APP.config['ALLOWED_EXTENSIONS'] = set(['wav'])

SIO = SocketIO(APP)

PROGRESS = {}

def MonitorProgess(hash):
    PROGRESS[hash] = {
        'split': {
            'total': 0,
            'progress' : 0,
        },
        'fft': {},
        'peak': {},
        'score': {},
    }

def CanProceeedToScore(hash):
    if not hash in PROGRESS:
        print('[web] Can\'t proceed: hash not found', hash)
        return False

    if PROGRESS[hash]['split']['total'] == 0 or PROGRESS[hash]['split']['progress'] < PROGRESS[hash]['split']['total']:
        print('[web] Can\'t proceed: Split', ROGRESS[hash]['split']['total'] , ROGRESS[hash]['split']['progress'])
        return False

    for key, data in PROGRESS[hash]['fft'].items():
        if data['total'] == 0 or data['progress'] < data['total']:
            print('[web] Can\' proceed: FFT', data['total'] , data['progress'])
            return False

    for key, data in PROGRESS[hash]['peak'].items():
        if data['total'] == 0 or data['progress'] < data['total']:
            print('[web] Can\' proceed: Peak', data['total'] , data['progress'])
            return False

    return True


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
            # TODO: Give a unique name to the temporary file
            filepath.EnsureExists('/data/temp-hash/raw')
            file.save('/data/temp-hash/raw')

            hash        = filepath.Hash('/data/temp-hash/raw')
            filename    = filepath.GetRawFromHash(hash)

            filepath.EnsureExists(filename)

            # Moving the temporary file to it's destination
            os.rename('/data/temp-hash/raw', filename)

            print('[web] File successfully uploaded. Saved as:' + filename)

            flash('[web] File successfully uploaded. Saved as:' + filename)

            MonitorProgess(hash)

            redis.open().lpush('JOB-QUEUE-SPLIT', hash)
            redis.open().publish('JOB-QUEUE-UPDATE-SPLIT', '')

            return redirect('/result/' + hash)
        else:
            flash('Only wav files are allowed')                                 # File doesn't have the correct expansion
            return redirect(request.url)

    # Make it pretty: https://www.jitsejan.com/python-and-javascript-in-flask.html


@APP.route('/result/<string:hash>')
def resultPage(hash):
    if hash in PROGRESS:
        return render_template('result.html.j2', hash=hash, fftProgress=PROGRESS[hash]['fft'], peakProgress=PROGRESS[hash]['peak'])
    else:
        return render_template('result.html.j2', hash=hash)


from flask_socketio import join_room, leave_room

@SIO.on('connect')
def onConnect():
    # print('[web] SIO:onConnect')
    return


@SIO.on('disconnect')
def onDisconnect():
    # print('[web] SIO:onDisconnect')
    return


@SIO.on('subscribe-to-hash')
def onSubscribeToHash(hash):
    print('[web] Client subscribed to hash:', hash)
    # TODO: perform verifications that the hash exist
    emit('server-answer', '[success] Subscribed to ' + hash)
    print('[web] Sent confirmation message', hash)
    SIO.emit('server-answer', 'Broadcast message - reason: a client subscribed to hash: ' + hash)
    join_room(hash)
    SIO.emit('server-answer', 'Room-wide message - reason: a client subscribed to hash: ' + hash, room=hash)


@SIO.on('request-update')
def onDisconnected(hash):
    if hash in PROGRESS:
        emit('update-split',    PROGRESS[hash]['split'])
        emit('update-fft',      PROGRESS[hash]['fft'])
        emit('update-peak',     PROGRESS[hash]['peak'])
        emit('update-score',    PROGRESS[hash]['score'])


def Dispatcher(message):
    # print('[web] Dispatching message:', message['channel'], message['data'])

    if message['channel'] == b'JOB-UPDATE-SPLIT':
        tokens = message['data'].decode('UTF-8').split('-')
        msg = tokens[1]

        if msg == 'STARTED':
            hash, total = tokens[0], int(tokens[2])

            PROGRESS[hash]['split']['total'] = total
        elif msg == 'UPDATE':
            hash, segmentHash   = tokens[0], tokens[2]
            progress, total     = int(tokens[3]), int(tokens[4])

            redis.open().lpush('JOB-QUEUE-FFT', hash + '-' + segmentHash)
            redis.open().publish('JOB-QUEUE-UPDATE-FFT', '')

            print('[web] Posted FFT job', hash + '-' + segmentHash, flush=True)

            PROGRESS[hash]['split']['progress'] = progress
            PROGRESS[hash]['fft'][segmentHash] = {
                'order': progress,
                'total': 0,
                'progress': 0,
                'hash': ''
            }
        elif msg == 'SUCCESS':
            hash = tokens[0]

            PROGRESS[hash]['split']['progress'] = PROGRESS[hash]['split']['total']
        else:
            print('[web] Recieved JOB-UPDATE-SPLIT', msg, flush=True)
            print('[web] This message is not handled', flush=True)

    elif message['channel'] == b'JOB-UPDATE-FFT':
        tokens = message['data'].decode('UTF-8').split('-')
        msg = tokens[2]

        if msg == 'STARTED':
            hash, segmentHash, total = tokens[0], tokens[1], int(tokens[3])

            PROGRESS[hash]['fft'][segmentHash]['total'] = total
        elif msg == 'UPDATE':
            hash, segmentHash   = tokens[0], tokens[1]
            progress, total     = int(tokens[3]), int(tokens[4])

            PROGRESS[hash]['fft'][segmentHash]['progress'] = progress
        elif msg == 'SUCCESS':
            hash, segmentHash, fftHash = tokens[0], tokens[1], tokens[3]

            print('[web] Posted Peak Job', hash + '-' + fftHash)
            redis.open().lpush('JOB-QUEUE-PEAK', hash + '-' + fftHash)
            redis.open().publish('JOB-QUEUE-UPDATE-PEAK', '')

            PROGRESS[hash]['peak'][fftHash] = {
                'order': PROGRESS[hash]['fft'][segmentHash]['order'],
                'total': 0,
                'progress': 0,
                'hash': ''
            }

            PROGRESS[hash]['fft'][segmentHash]['hash'] = fftHash
            PROGRESS[hash]['fft'][segmentHash]['progress'] = PROGRESS[hash]['fft'][segmentHash]['total']
        else:
            print('[web] Recieved JOB-UPDATE-FFT', msg)
            print('[web] This message is not handled')

    elif message['channel'] == b'JOB-UPDATE-PEAK':
        tokens = message['data'].decode('UTF-8').split('-')
        msg = tokens[2]

        if msg == 'STARTED':
            hash, fftHash, total = tokens[0], tokens[1], int(tokens[3])

            PROGRESS[hash]['peak'][fftHash]['total'] = total
        elif msg == 'UPDATE':
            hash, fftHah    = tokens[0], tokens[1]
            progress, total = int(tokens[3]), int(tokens[4])

            PROGRESS[hash]['peak'][fftHah]['progress'] = progress
        elif msg == 'SUCCESS':
            hash, fftHash, peakHash = tokens[0], tokens[1], tokens[3]

            PROGRESS[hash]['peak'][fftHash]['hash'] = peakHash
            PROGRESS[hash]['peak'][fftHash]['progress'] = PROGRESS[hash]['peak'][fftHash]['total']

            print('[web] Recived SUCCESS message from a Peak Job. Trying to proceed to Score...', CanProceeedToScore(hash))

            # Test if all FFT and all PEAK jobs are complete
            if CanProceeedToScore(hash):
                redis.open().lpush('JOB-QUEUE-SCORE', hash)
                redis.open().publish('JOB-QUEUE-UPDATE-SCORE', '')
                print('[web] Published Score job:', hash)
        else:
            print('[web] Recieved JOB-UPDATE-PEAK', msg)
            print('[web] This message is not handled')

    elif message['channel'] == b'WORKER-STOP':
        Stop()
    else:
        print('[web] Message was not handled:', message['channel'], message['data'])


redisSubscribe          = None
redisSubscribeThread    = None

def Stop():
    global redisSubscribe, redisSubscribeThread

    redisSubscribeThread.stop()
    redisSubscribe.close()


if __name__ == "__main__":
    print('[web] Starting...')

    redisSubscribe = redis.open().pubsub()
    redisSubscribe.subscribe(**{'JOB-UPDATE-SPLIT': Dispatcher})
    redisSubscribe.subscribe(**{'JOB-UPDATE-FFT': Dispatcher})
    redisSubscribe.subscribe(**{'JOB-UPDATE-PEAK': Dispatcher})
    redisSubscribe.subscribe(**{'WORKER-STOP': Dispatcher})
    redisSubscribe.subscribe(**{'DUMMY_CHANNEL': Dispatcher})
    redisSubscribeThread = redisSubscribe.run_in_thread(sleep_time=0.5)

    print('[web] Suscribed to Redis')

    # InitDB()
    SIO.run(APP, host='0.0.0.0', port=5000)
    print('[web] Awaiting requests...')
    # CloseDB()
