__author__ = 'flanker'


class InvalidRepositoryException(BaseException):
    def __init__(self, msg):
        self.msg = msg

    def __unicode__(self):
        return self.msg

    def __str__(self):
        return self.msg
