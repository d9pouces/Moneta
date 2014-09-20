"""
Utility module providing nice (colorized) logger.

"""
from bz2 import BZ2Decompressor
import copy
import gzip
import logging
import logging.handlers
import os
import shutil
import stat
import tempfile
import unicodedata
import zlib

from django.conf import settings
from django.core import exceptions
from django.http import QueryDict
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _
import time


class ColorizedHandler(logging.StreamHandler):
    """Basic :class:`logging.StreamHandler` modified to colorize its output
    according to the record level.
    """

    def emit(self, record):
        """Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream."""
        myrecord = copy.copy(record)
        levelno = myrecord.levelno
        if levelno >= 50:
            color = '\x1b[31m'  # red
        elif levelno >= 40:
            color = '\x1b[31m'  # red
        elif levelno >= 30:
            color = '\x1b[33m'  # yellow
        elif levelno >= 20:
            color = '\x1b[32m'  # green
        elif levelno >= 10:
            color = '\x1b[35m'  # pink
        else:
            color = '\x1b[0m'  # normal
        myrecord.msg = color + myrecord.msg + '\x1b[0m'  # normal
        return logging.StreamHandler.emit(self, myrecord)


def import_path(middleware_path):
    try:
        mw_module, mw_fnname = middleware_path.rsplit('.', 1)
    except ValueError:
        raise exceptions.ImproperlyConfigured('%s isn\'t a middleware module' % middleware_path)
    try:
        mod = import_module(mw_module)
    except ImportError as e:
        raise exceptions.ImproperlyConfigured('Error importing middleware %s: "%s"' % (mw_module, e))
    try:
        mw_fn = getattr(mod, mw_fnname)
    except AttributeError:
        raise exceptions.ImproperlyConfigured(
            'Middleware module "%s" does not define "%s"' % (mw_module, mw_fnname))
    return mw_fn


def remove(path):
    """
    Remove the path given in argument. All files must belong to the current user.
    :param path:
    """
    result = True
    if os.path.exists(path):
        # noinspection PyBroadException
        try:
            for root, dirs, files in os.walk(path, topdown=True):
                for name in files:
                    if not os.path.islink(os.path.join(root, name)):
                        os.chmod(os.path.join(root, name), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                for name in dirs:
                    os.chmod(os.path.join(root, name), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            if os.path.isfile(path):
                os.remove(path)
            if os.path.isdir(path):
                shutil.rmtree(path)
        except Exception:
            result = False
            logging.warning(_('Unable to remove %(path)s.') % {'path': path, }, exc_info=True)
    return result


def rename(src, dst):
    result = True
    # noinspection PyBroadException
    try:
        if not makedir(dst):
            return False
        if not remove(dst):
            return False
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        remove(src)
    except Exception:
        result = False
        logging.warning(_('Unable to rename %(src)s to %(dst)s.') % {'src': src, 'dst': dst, }, exc_info=True)
    return result


def makedir(path):
    result = True
    # noinspection PyBroadException
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except Exception:
        result = False
        logging.warning(_('Unable to create directory %(path)s.') % {'path': path, }, exc_info=True)
    return result


def normalize_str(x):
    """
    Normalize strings by changing uppercase chars to lowercase, and removing accents
    :param x: the string to normalize
    :return: the normalized string
    """
    return unicodedata.normalize('NFKD', x.lower()).encode('ASCII', 'ignore')


def mkdtemp():
    """
    create a temporary directory inside the settings.TEMP_ROOT
    :return: the name of the created directory
    """
    makedir(settings.TEMP_ROOT)
    return tempfile.mkdtemp(dir=settings.TEMP_ROOT, prefix='moneta')


def read_file_in_chunks(fileobj, chunk_size=4096):
    while True:
        data = fileobj.read(chunk_size)
        if not data:
            break
        yield data


class ZlibFile(object):
    def __init__(self, fileobj):
        self.__fileobj = fileobj
        self.__decompressor = zlib.decompressobj()
        self.__is_flushed = False

    def read(self, bufsize=10240):
        uncompressed_data = ''
        while not uncompressed_data and not self.__is_flushed:
            compressed_data = self.__fileobj.read(bufsize)
            if not compressed_data:
                self.__is_flushed = True
                uncompressed_data = self.__decompressor.flush()
            else:
                uncompressed_data = self.__decompressor.decompress(compressed_data)
        return uncompressed_data

    def close(self):
        pass


class BZ2File(object):
    def __init__(self, fileobj):
        self.__fileobj = fileobj
        self.__is_finished = False
        self.__decompressor = BZ2Decompressor()

    def read(self, bufsize):
        uncompressed_data = ''
        while not uncompressed_data and not self.__is_finished:
            compressed_data = self.__fileobj.read(bufsize)
            if not compressed_data:
                self.__is_finished = True
            else:
                uncompressed_data = self.__decompressor.decompress(compressed_data)
        return uncompressed_data

    def close(self):
        pass


def split_lines(fd, compression=None, bufsize=10240):
    __buffer = ''
    if compression == 'gz':
        tmp_file = tempfile.TemporaryFile()
        data = fd.read(bufsize)
        while data:
            tmp_file.write(data)
            data = fd.read(bufsize)
        tmp_file.seek(0)
        fd = gzip.GzipFile('filename', 'r', 9, fileobj=tmp_file)
    elif compression == 'bz2':
        fd = BZ2File(fd)
    data = fd.read(bufsize)
    while data:
        pos = data.find("\n")
        while pos > -1:
            if __buffer:
                yield __buffer + data[0:pos]
                __buffer = ''
            else:
                yield data[0:pos]
            data = data[pos + 1:]
            pos = data.find("\n")
        __buffer += data
        data = fd.read(bufsize)
    yield __buffer
    fd.close()


def parse_control_data(control_data, continue_line=' ', split=': ', skip_after_blank=False):
    offset = len(continue_line)
    result_data = QueryDict('', mutable=True)
    key, value = None, None
    description = ''
    add_to_description = False
    for line in control_data.splitlines():
        if not line.split() and skip_after_blank:
            add_to_description = True
        if add_to_description:
            description += "\n"
            description += line
            continue
        if not line or line[0:offset] == continue_line:
            if key is not None:
                value += "\n"
                value += line[offset:]
        else:
            if key is not None:
                if key not in result_data:
                    result_data.setlist(key, [value])
                else:
                    result_data.appendlist(key, value)
            key, value = line.split(split, 1)
            value = value.lstrip()
    if key is not None:
        if key not in result_data:
            result_data.setlist(key, [value])
        else:
            result_data.appendlist(key, value)
    if add_to_description:
        result_data.setlist('description', [description])
    return result_data
