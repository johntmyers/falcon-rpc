import falcon_rpc


class Test:
    """``test`` method family """

    def ok(self, req):
        # /test.ok
        req.resp_body = {'foo': 'bar'}

    def error(self, req):
        # /test.error
        # can raise an error at anytime
        raise falcon_rpc.RPCError('dummy_error_code')

    def fatal(self, req):
        # /test.unhandled
        not_a_dict = 1
        not_a_dict['nope'] = 2  # pylint: disable=unsupported-assignment-operation  # noqa

    def echo(self, req):
        # /test.echo
        req.resp_body = {'you_sent': req.params}

    def warn(self, req):
        # /test.warn
        req.resp_body = {'data': 'mostly good'}
        # setting a warning even though the request was handled
        req.set_warning('some_warning')

    def redirect(self, req):
        # /test.redirect
        raise falcon_rpc.RPCRedirect('http://www.google.com')


class Another:

    def show_me(self, req):
        # req.req is the original Falcon Request object
        req.resp_body = {'hello_there': req.req.remote_addr}


def start():
    rpc = falcon_rpc.RPC()
    rpc.add_family(Test())
    rpc.add_family(Another())
    return rpc()
