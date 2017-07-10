from xmlrpc.client import dumps, Fault, loads
from django.http.response import HttpResponse


class XMLRPCSite(object):
    def __init__(self):
        self.methods = {}

    def register_method(self, func, name=None):
        if name is None:
            name = func.__name__
        self.methods[name] = func

    def dispatch(self, request, *args, **kwargs):
        rpc_call = loads(request.body.decode('utf-8'))
        rpc_args = rpc_call[0]
        method_name = rpc_call[1]
        try:
            # noinspection PyCallingNonCallable
            src_result = self.methods[method_name](request, rpc_args, *args, **kwargs)
            result = src_result,
        except Exception as e:
            result = Fault(e.__class__.__name__, str(e))
        data = dumps(result, method_name, True)
        return HttpResponse(data, content_type='application/xml+rpc')


def register_rpc_method(site, name=None):
    def decorated(func):
        site.register_method(func, name=name)
        return func
    return decorated
