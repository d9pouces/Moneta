"""
PyRPM
=====

PyRPM is a pure python, simple to use, module to read information from a RPM file.
"""

from collections import namedtuple
import hashlib
import re
import stat
import struct
import sys

if sys.version < '3':
    try:
        from io import StringIO as BytesIO
    except ImportError:
        from io import StringIO as BytesIO
else:
    from io import BytesIO


class Entry(object):
    """ RPM Header Entry """

    # noinspection PyShadowingBuiltins
    def __init__(self, entry=None, store=None, tag=None, type=None, value=None):
        # noinspection PyPep8Naming
        DECODING_MAP = {
            0: self._read_null,
            1: self._read_char,
            2: self._read_int8,
            3: self._read_int16,
            4: self._read_int32,
            5: self._read_int64,
            6: self._read_string,
            7: self._read_binary,
            8: self._read_string_array,
            9: self._read_string,
        }

        # read from file if possible
        if entry is not None and store is not None:
            # seek to position in store
            store.seek(entry[2])

            # decode information
            self.entry = entry
            self.tag = entry[0]
            self.type = entry[1]
            self.value = DECODING_MAP[entry[1]](store, entry[3])
        else:
            self.tag = tag
            self.type = type
            self.value = value

    def __str__(self):
        return "(%s, %s)" % (self.tag, self.value, )

    def __repr__(self):
        return "(%s, %s)" % (self.tag, self.value, )

    @staticmethod
    def _read_format(fmt, store):
        size = struct.calcsize(fmt)
        data = store.read(size)
        unpacked_data = struct.unpack(fmt, data)
        return unpacked_data[0] if len(unpacked_data) == 1 else unpacked_data

    # noinspection PyUnusedLocal
    @staticmethod
    def _read_null(store, data_count):
        return None

    def _read_char(self, store, data_count):
        """ store is a pointer to the store offset
        where the char should be read
        """
        return self._read_format('!{0:d}s'.format(data_count), store)

    def _read_int8(self, store, data_count):
        """ int8 = 1byte
        """
        return int(self._read_char(store, data_count))

    def _read_int16(self, store, data_count):
        """ int16 = 2bytes
        """
        return self._read_format('!{0:d}h'.format(data_count), store)

    def _read_int32(self, store, data_count):
        """ int32 = 4bytes
        """
        return self._read_format('!{0:d}i'.format(data_count), store)

    def _read_int64(self, store, data_count):
        """ int64 = 8bytes
        """
        return self._read_format('!{0:d}q'.format(data_count), store)

    def _read_string(self, store, data_count):
        """ read a string entry
        """
        string = b''
        while True:
            char = self._read_char(store, 1)
            if char == b'\x00':  # read until '\0'
                break
            string += char
        return string.decode('utf-8')

    def _read_string_array(self, store, data_count):
        """ read a array of string entries
        """
        return [self._read_string(store, 1) for i in range(data_count)]

    def _read_binary(self, store, data_count):
        """ read a binary entry
        """
        return self._read_format('!{0:d}s'.format(data_count), store)


# noinspection PyBroadException
class HeaderBase(object):

    """ RPM Header Structure """
    MAGIC_NUMBER = b'\x8e\xad\xe8'
    MAGIC_NUMBER_MATCHER = re.compile(b'(\x8e\xad\xe8)')

    TAGS = {}

    def __init__(self, file):
        """ read a RPM header structure with all its entries

            Header format:
            [3bytes][1byte][4bytes][4bytes][4bytes]
              MN      VER   UNUSED  IDXNUM  STSIZE

            Entry format:
            [4bytes][4bytes][4bytes][4bytes]
               TAG    TYPE   OFFSET  COUNT
        """
        self.entries = []

        # read from file if possible
        if file:
            # read and check header
            start = file.tell()
            header = struct.unpack('!3sc4sll', file.read(16))
            if header[0] != self.MAGIC_NUMBER:
                raise RPMError('invalid RPM header')

            # read entries and store
            entries = [file.read(16) for i in range(header[3])]
            store = BytesIO(file.read(header[4]))

            # parse entries
            for entry in entries:
                parsed_entry = struct.unpack("!4l", entry)
                object_entry = Entry(parsed_entry, store)

                if object_entry:
                    self.entries.append(object_entry)
            end = file.tell()
            self.header_range = (start, end)

    def __getattr__(self, name):
        if name in self.TAGS:
            id_, default = self.TAGS[name]
            try:
                return self[id_]
            except:
                return default

        raise AttributeError(name)

    def __iter__(self):
        for entry in self.entries:
            yield entry

    def __getitem__(self, item):
        for entry in self:
            if entry.tag == item:
                return entry.value
        raise KeyError()


# signature header section
class Signature(HeaderBase):
    TAGS = {
        'size': (1000, -1),
        'pgp': (1002, ""),
        'md5': (1004, ""),
        'gpg': (1005, ""),
        'pgp5': (1006, ""),
        'payload_size': (1007, -1),
    }


# primary header section
class Header(HeaderBase):
    TAGS = {
        'name': (1000, ""),
        'version': (1001, "0.1"),
        'release': (1002, ""),
        'epoch': (1003, 0),
        'summary': (1004, ""),
        'description': (1005, ""),
        'build_time': (1006, 0),
        'build_host': (1007, ""),
        'size': (1009, 0),
        'vendor': (1011, ""),
        'license': (1014, ""),
        'packager': (1015, ""),
        'group': (1016, []),
        'url': (1020, ""),
        'architecture': (1022, ""),
        'source_rpm': (1044, ""),
        'archive_size': (1046, 0),
        'provides': (1047, []),
        'requires': (1049, []),
        'conflicts': (1054, []),
        'platform': (1132, ""),
    }


class RPMError(BaseException):
    pass


RPMFile = namedtuple("RPMFile", ['name', 'size', 'mode', 'rdevice', 'device', 'time', 'digest', 'link_to',
                     'flags', 'username', 'group', 'verify_flags', 'language', 'inode', 'color', 'content_class', 'type', 'primary'])
RPMChangeLog = namedtuple("RPMChangeLog", ['name', 'text', 'time'])
RPMprco = namedtuple("RPMprco", ['name', 'version', 'flags', 'str_flags'])


# noinspection PyPep8Naming,PyBroadException
class RPM(object):
    RPM_LEAD_MAGIC_NUMBER = b'\xed\xab\xee\xdb'
    RPM_PRCO_FLAGS_MAP = {0: None, 2: 'LT', 4: 'GT', 8: 'EQ', 10: 'LE', 12: 'GE'}

    def __init__(self, rpm):
        """ rpm - StringIO.StringIO/io.BytesIO | file
        """
        if hasattr(rpm, 'read'):  # if it walk like a duck..
            self.rpmfile = rpm
        else:
            raise ValueError('invalid initialization: StringIO/BytesIO or file expected received %s' % (type(rpm), ))

        self.binary = None
        self.source = None
        self.header = None
        self.signature = None
        self.filelist = []
        self.changelog = []

        self.provides = []
        self.requires = []
        self.obsoletes = []
        self.conflicts = []

        self._read_lead()
        self._read_signature()
        self._read_header()
        self._match_composite()
        self._compute_checksum()

    @property
    def canonical_filename(self):
        if self.header.epoch == 0:
            return "%s-%s-%s.%s.rpm" % (self.header.name, self.header.version, self.header.release, self.header.architecture if self.binary else "src")
        else:
            return "%s-%s-%s-%d.%s.rpm" % (self.header.name, self.header.version, self.header.release, self.header.epoch, self.header.architecture if self.binary else "src")

    def _read_lead(self):
        """ reads the rpm lead section

            struct rpmlead {
               unsigned char magic[4];
               unsigned char major, minor;
               short type;
               short archnum;
               char name[66];
               short osnum;
               short signature_type;
               char reserved[16];
               } ;
        """
        lead_fmt = '!4sBBhh66shh16s'
        data = self.rpmfile.read(96)
        value = struct.unpack(lead_fmt, data)

        magic_num = value[0]
        ptype = value[3]

        if magic_num != self.RPM_LEAD_MAGIC_NUMBER:
            raise RPMError('wrong magic number this is not a RPM file')

        if ptype == 1:
            self.binary = False
            self.source = True
        elif ptype == 0:
            self.binary = True
            self.source = False
        else:
            raise RPMError('wrong package type this is not a RPM file')

    def _read_signature(self):
        """ read signature header """

        # find the start of the header
        if not self._find_magic_number():
            raise RPMError('invalid RPM file, signature area not found')

        # consume signature area
        self.signature = Signature(self.rpmfile)

    def _read_header(self):
        """ read information header """

        # find the start of the header
        if not self._find_magic_number():
            raise RPMError('invalid RPM file, header not found')

        # consume header area
        self.header = Header(self.rpmfile)

    def _find_magic_number(self):
        """ find a magic number in a buffer
        """
        string = self.rpmfile.read(1)
        while True:
            match = HeaderBase.MAGIC_NUMBER_MATCHER.search(string)
            if match:
                self.rpmfile.seek(-3, 1)
                return True
            byte = self.rpmfile.read(1)
            if not byte:
                return False
            else:
                string += byte
        return False

    def _match_composite(self):
        # files
        try:
            for idx, name in enumerate(self.header[1117]):
                dirname = self.header[1118][self.header[1116][idx]]
                self.filelist.append(RPMFile(
                    name=dirname + name,
                    size=self.header[1028][idx],
                    mode=self.header[1030][idx],
                    rdevice=self.header[1033][idx],
                    time=self.header[1034][idx],
                    digest=self.header[1035][idx],
                    link_to=self.header[1036][idx],
                    flags=self.header[1037][idx],
                    username=self.header[1039][idx],
                    group=self.header[1040][idx],
                    verify_flags=self.header[1045][idx],
                    device=self.header[1095][idx],
                    inode=self.header[1096][idx],
                    language=self.header[1097][idx],
                    color=self.header[1140][idx] if 1140 in self.header else None,
                    content_class=self.header[1142][self.header[1141][idx]] if 1142 in self.header and 1141 in self.header else None,
                    type='dir' if stat.S_ISDIR(self.header[1030][idx] & 65535) else ('ghost' if (self.header[1037][idx] & 64) else 'file'),
                    primary=('bin/' in dirname or dirname.startswith('/etc/'))))
        except:
            pass

        # change log
        try:
            if self.header[1081]:
                for name, time, text in zip(self.header[1081], self.header[1080], self.header[1082]):
                    self.changelog.append(RPMChangeLog(name=name, time=time, text=text))
        except:
            pass

        # provides
        try:
            if self.header[1047]:
                for name, flags, version in zip(self.header[1047], self.header[1112], self.header[1113]):
                    self.provides.append(
                        RPMprco(name=name, flags=flags, str_flags=self.RPM_PRCO_FLAGS_MAP[flags & 0xf], version=self._stringToVersion(version)))
        except:
            pass

        # requires
        try:
            if self.header[1049]:
                for name, flags, version in zip(self.header[1049], self.header[1048], self.header[1050]):
                    self.requires.append(
                        RPMprco(name=name, flags=flags, str_flags=self.RPM_PRCO_FLAGS_MAP[flags & 0xf], version=self._stringToVersion(version)))
        except:
            pass

        # obsoletes
        try:
            if self.header[1090]:
                for name, flags, version in zip(self.header[1090], self.header[1114], self.header[1115]):
                    self.obsoletes.append(
                        RPMprco(name=name, flags=flags, str_flags=self.RPM_PRCO_FLAGS_MAP[flags & 0xf], version=self._stringToVersion(version)))
        except:
            pass

        # conflicts
        try:
            if self.header[1054]:
                for name, flags, version in zip(self.header[1054], self.header[1053], self.header[1055]):
                    self.conflicts.append(
                        RPMprco(name=name, flags=flags, str_flags=self.RPM_PRCO_FLAGS_MAP[flags & 0xf], version=self._stringToVersion(version)))
        except:
            pass

    def _compute_checksum(self):
        self.rpmfile.seek(0)
        m = hashlib.sha256()
        size = 0
        data = self.rpmfile.read()
        while data:
            size += len(data)
            m.update(data)
            data = self.rpmfile.read()
        self.filesize = size
        self.checksum = m.hexdigest()

    def _stringToVersion(self, verstring):
        if verstring in [None, '']:
            return None, None, None
        i = verstring.find(':')
        if i != -1:
            try:
                epoch = str(int(verstring[:i]))
            except ValueError:
                # look, garbage in the epoch field, how fun, kill it
                epoch = '0'  # this is our fallback, deal
        else:
            epoch = '0'
        j = verstring.find('-')
        if j != -1:
            if verstring[i + 1:j] == '':
                version = None
            else:
                version = verstring[i + 1:j]
            release = verstring[j + 1:]
        else:
            if verstring[i + 1:] == '':
                version = None
            else:
                version = verstring[i + 1:]
            release = None
        return epoch, version, release
