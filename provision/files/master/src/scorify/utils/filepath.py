import os

DATA_FOLDER = '/data'


def Hash(filename):
    """ Returns a hash that uniquely indentify a file
            > file: file opened in 'rb' mode
    """
    import hashlib

    with open(filename, 'rb') as file:
        hash = hashlib.md5()
        while True:
            data = file.read(65536)

            if not data:
                break

            hash.update(data)

    return hash.hexdigest()


def GetRawFromHash(hash):
    return os.path.join(DATA_FOLDER, hash, 'raw')


def GetSegmentFromHash(hash, segmentHash):
    return os.path.join(DATA_FOLDER, hash, 'segment', segmentHash)


def GetFFTFromHash(hash, fftHash):
    return os.path.join(DATA_FOLDER, hash, 'fft', fftHash)


def GetPeakFromHash(hash, peakHash):
    return os.path.join(DATA_FOLDER, hash, 'peak', peakHash)


def GetDirectoryFromHash(hash, sub):
    if sub:
        return os.path.join(DATA_FOLDER, hash, sub)
    else:
        return os.path.join(DATA_FOLDER, hash)


def EnsureExists(filepath):
    dirname = os.path.dirname(filepath)

    if not os.path.isdir(dirname):
        print('[utils] Creating', dirname)
        os.makedirs(dirname)
