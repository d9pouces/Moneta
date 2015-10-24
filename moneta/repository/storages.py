# coding=utf-8
import mimetypes
import os
import shutil
from moneta.utils import makedir, remove

__author__ = 'flanker'

mimetypes.init()


class BaseStorage(object):
    # noinspection PyPep8Naming
    def __init__(self, ENGINE=''):
        """
        Initialise the storage backend
        :param ENGINE: class of this storage backend
        """
        self.engine = ENGINE

    def store(self, uid, path):
        """
        Store the directory in its internal storage (can be a zip file, or flat files)
        :param uid: UUID of the Element
        :param path: absolute path to store
        :return: a key unique to this storage
        :raise:
        """
        raise NotImplementedError

    def list_dir(self, key, sub_path):
        """
        List elements (directories and files) in a given directory
        :param key: UUID of the Element
        :param sub_path: relative path of the directory to list
        :return: A tuple of lists (directory names, file names)
        :raise:
        """
        for root, dirs, files in self.walk(key, sub_path):
            return dirs, files

    def walk(self, key, sub_path):
        """
        List elements (directories and files) in a given directory
        :param key: UUID of the Element
        :param sub_path: relative path of the directory to list
        :return: Same thing as os.walk
        :raise:
        """
        raise NotImplementedError

    def store_descriptor(self, uid, filename, fd):
        """
        Store a file content given by a file descriptor
        :param uid: UUID of the Element
        :param fd: file descriptor
        :return: a key unique to this storage
        :raise:
        """
        raise NotImplementedError

    def get_file(self, key, sub_path='', mode='rb'):
        """
        Return a file descriptor in read mode of the given path
        :param key: UUID of the Element
        :param sub_path: relative path to read
        :return: A file-like object
        :raise:
        """
        raise NotImplementedError

    def get_path(self, key, sub_path):
        """ return an absolute path of the file, or None if does not exist (e.g., database storage).

        :param key: UUID of the Element
        :param sub_path: relative path to read
        :return: `str`
        :raise:
        """
        raise NotImplementedError

    def get_relative_path(self, key, sub_path):
        """ return an relative path of the file to the root, or None if does not exist (e.g., database storage).

        :param key: UUID of the Element
        :param sub_path: relative path to read
        :return: `str`
        :raise:
        """
        raise NotImplementedError

    def delete(self, key):
        """
        Delete the element from its internal storage
        :param key: UUID of the Element to delete
        :raise:
        """
        raise NotImplementedError

    def import_filename(self, filename, key, sub_path=''):
        """import the filename to the storage. Remove the local source filename!

        :param key: UUID of the Element
        :param sub_path: relative path to read
        :return:
        :rtype: :class:`bool`
        """
        raise NotImplementedError

    def get_size(self, key, sub_path):
        """
        Return the file size
        :param key: UUID of the Element to delete
        :raise:
        """
        raise NotImplementedError

    def uid_to_key(self, uid):
        raise NotImplementedError

    def mimetype(self, key, sub_path):
        raise NotImplementedError


class FlatStorage(BaseStorage):
    # noinspection PyPep8Naming
    def __init__(self, ENGINE='', ROOT=None, PATH_LEN=1):
        self.root = os.path.abspath(ROOT)
        self.path_len = PATH_LEN
        super(FlatStorage, self).__init__(ENGINE=ENGINE)

    def uid_to_key(self, uid):
        return os.path.join(*(self.split_uid(uid) + [uid]))

    def store(self, uid, path):
        """
        Store the directory in its internal storage (can be a zip file, or flat files)
        :param uid: UUID of the Element
        :param path: absolute path to store
        :return: a key unique to this storage
        :raise:
        """
        components = [self.root] + self.split_uid(uid) + [uid]
        components.append(os.path.basename(path))
        shutil.copytree(path, os.path.join(*components))
        return self.uid_to_key(uid)

    def list_dir(self, key, sub_path):
        """
        List elements (directories and files) in a given directory
        :param key: UUID of the Element
        :param sub_path: relative path of the directory to list
        :return: A tuple of lists (directory names, file names)
        :raise:
        """
        for root, dirs, files in self.walk(key, sub_path):
            return dirs, files

    def walk(self, key, sub_path):
        """
        List elements (directories and files) in a given directory
        :param key: UUID of the Element
        :param sub_path: relative path of the directory to list
        :return: Same behaviour as os.walk
        :raise:
        """
        components = [self.root, key]
        root_path = os.path.abspath(os.path.join(*components))
        if sub_path:
            components.append(sub_path)
        path = os.path.abspath(os.path.join(*components))
        if os.path.isfile(path):
            return self.simple_generator(
                (os.path.relpath(os.path.dirname(path), root_path), (), (os.path.basename(path), )))
        else:
            return self.rel_generator(os.walk(path), root_path)

    # noinspection PyMethodMayBeStatic
    def rel_generator(self, walker, root_path):
        for root, dirs, files in walker:
            yield os.path.relpath(root, root_path), dirs, files

    # noinspection PyMethodMayBeStatic
    def simple_generator(self, lis):
        yield lis

    def get_file(self, key, sub_path='', mode='rb'):
        """
        Return a file descriptor in read mode of the given path
        :param key: UUID of the Element
        :param sub_path: relative path to read
        :return: A file-like object
        :raise:
        """
        components = [self.root, key]
        if sub_path:
            components.append(sub_path)
        abs_path = os.path.join(*components)
        makedir(os.path.dirname(abs_path))
        try:
            fd = open(abs_path, mode)
        except IOError:
            fd = None
        return fd

    def import_filename(self, filename, key, sub_path=''):
        components = [self.root, key]
        if sub_path:
            components.append(sub_path)
        abs_path = os.path.join(*components)
        makedir(os.path.dirname(abs_path))
        return os.rename(filename, abs_path)

    def get_path(self, key, sub_path):
        """ return an absolute path of the file, or None if does not exist (e.g., database storage).

        :param key: UUID of the Element
        :param sub_path: relative path to read
        :return: `str`
        :raise:
        """
        components = [self.root, key]
        if sub_path:
            components.append(sub_path)
        return os.path.join(*components)

    def get_relative_path(self, key, sub_path):
        """ return an relative path of the file to the root, or None if does not exist (e.g., database storage).

        :param key: UUID of the Element
        :param sub_path: relative path to read
        :return: `str`
        :raise:
        """
        return os.path.relpath(self.get_path(key, sub_path), self.root)

    def get_size(self, key, sub_path):
        components = [self.root, key]
        if sub_path:
            components.append(sub_path)
        return os.path.getsize(os.path.join(*components))

    def delete(self, key):
        """
        Delete the element from its internal storage
        :param key: UUID of the Element to delete
        :raise:
        """
        abs_path = os.path.join(self.root, key)

        def remove_dir(dirname):
            """
            recursively delete empty directories
            :param dirname: directory to remove
            :return: None
            """
            if not os.path.exists(dirname):
                return
            if len(os.listdir(dirname)) > 0 or dirname == self.root:
                return
            remove(dirname)
            remove_dir(os.path.dirname(dirname))

        result = remove(abs_path)
        remove_dir(os.path.dirname(abs_path))
        return result

    def store_descriptor(self, uid, filename, fd):
        """
        Store a file content given by a file descriptor
        :param uid: UUID of the Element
        :param fd: file descriptor
        :return: a key unique to this storage
        :raise:
        """
        components = [self.root] + self.split_uid(uid) + [uid, filename]
        abs_path = os.path.join(*components)
        makedir(os.path.dirname(abs_path))
        with open(abs_path, 'wb') as fd_write:
            data = fd.read(10240)
            while data:
                fd_write.write(data)
                data = fd.read(10240)
        return os.path.join(*(components[1:]))

    def split_uid(self, uid):
        return [x for x in uid[0:self.path_len]]

    def mimetype(self, key, sub_path):
        path = self.get_path(key, sub_path)
        return mimetypes.guess_type(path)[0] or 'application/octet-stream'


if __name__ == '__main__':
    import doctest

    doctest.testmod()
