# coding=utf-8
import os
from tarfile import InvalidHeaderError

__author__ = 'flanker'


class ArInfo(object):
    def __init__(self, name=''):
        self.name = name
        self.size = 0
        self.timestamp = 0
        self.owner_id = 0
        self.group_id = 0
        self.file_mode = 0


class ArObjFile(object):
    def __init__(self, fileobj, file_size, bufsize=10240):
        self.bufsize = bufsize
        self.fileobj = fileobj
        self.file_size = file_size
        self.seek_offset = self.fileobj.tell()
        self.read_size = 0

    @staticmethod
    def seekable():
        return True

    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            self.read_size = offset
        elif whence == os.SEEK_CUR:
            self.read_size += offset
        elif whence == os.SEEK_END:
            self.read_size = self.file_size + offset
        self.fileobj.seek(self.read_size + self.seek_offset)

    def read(self, size=None):
        if size is None:
            size = self.file_size - self.read_size
        size = min(self.file_size - self.read_size, size)
        self.read_size += size
        return self.fileobj.read(size)

    def close(self):
        pass

    def tell(self):
        return self.read_size


class ArFile(object):
    GLOBAL_HEADER = b'!<arch>\n'

    def __init__(self, name=None, mode='r', fileobj=None, bufsize=10240):
        self.name = name
        self.mode = mode[0]
        self.fileobj = fileobj
        self.bufsize = bufsize
        if fileobj is None:
            self.fileobj = open(name, self.mode + 'b')
        if self.mode == 'r':
            if self.fileobj.read(8) != self.GLOBAL_HEADER:
                raise InvalidHeaderError
        else:
            self.fileobj.write(self.GLOBAL_HEADER)
        self.__current_pos = self.fileobj.tell()

    def __reset(self):
        self.fileobj.seek(0)
        if self.fileobj.read(8) != self.GLOBAL_HEADER:
            raise InvalidHeaderError
        self.__current_pos = 8

    def getmember(self, name):
        self.__reset()
        ar_info = self.next()
        while ar_info is not None and ar_info.name != name:
            ar_info = self.next()
        return ar_info

    def getmembers(self):
        self.__reset()
        members = []
        ar_info = self.next()
        while ar_info is not None:
            members.append(ar_info)
            ar_info = self.next()
        return members

    def getnames(self):
        self.__reset()
        members = []
        ar_info = self.next()
        while ar_info is not None:
            members.append(ar_info.name)

            ar_info = self.next()
        return members

    def next(self):
        self.fileobj.seek(self.__current_pos)
        data = self.fileobj.read(60)
        magic = data[58:60]  # byte
        if magic != b'\x60\x0a':
            return None
        assert isinstance(data, bytes)
        ar_info = ArInfo(data[0:16].decode('utf-8').strip())
        ar_info.filename = data[0:16].decode('utf-8').strip()
        ar_info.timestamp = data[16:28]
        ar_info.owner_id = data[28:34]
        ar_info.group_id = data[34:40]
        ar_info.file_mode = data[40:48]
        ar_info.size = int(data[48:58])
        self.__current_pos += (60 + int((ar_info.size + 1) / 2) * 2)
        return ar_info

    def extractall(self, path='.', members=None):
        members = set([x.name for x in members]) if members is not None else None
        self.__reset()
        member = self.next()
        while member is not None:
            if members is None or member.name in members:
                fullpath = os.path.join(path, member.name)
                e = ArObjFile(self.fileobj, member.size)
                with open(fullpath, 'wb') as fd:
                    data = e.read(self.bufsize)
                    while data:
                        fd.write(data)
                        data = e.read(self.bufsize)
            member = self.next()

    def extract(self, member, path=''):
        self.__reset()
        if not isinstance(member, ArInfo):
            member = ArInfo(name=member)
        return self.extractall(path=path, members=(member, ))

    def extractfile(self, member):
        name = member.name if isinstance(member, ArInfo) else member
        self.__reset()
        member = self.next()
        while member is not None:
            if member.name == name:
                return ArObjFile(self.fileobj, member.size)
            member = self.next()

    def add(self, name, arcname=None):
        pass

    def addfile(self, arinfo, fileobj=None):
        pass

    def getarinfo(self, name=None, arcname=None, fileobj=None):
        pass

    def close(self):
        pass

if __name__ == '__main__':
    import doctest

    doctest.testmod()
