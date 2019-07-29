"""Falcon RPC"""
import json
import copy

import falcon
from falcon_cors import CORS

import falcon_rpc.errors as errors
from falcon_rpc.logger_ext import get_logger

logger = get_logger(__name__)


URL_ENCODED = 'urlencoded_string'


def _json_error_serializer(req, resp, exception):
    """We don't convert the exception to JSON
    since the response interceptor will handle
    that for us """
    resp.body = exception.to_dict()


def _get_post_data(req, resp, resource, params):
    """Set the context object in the request with
    our POST data. If we received JSON, attempt to load
    and use that. Otherwise, we'll use the existing params
    """
    if req.content_type in (falcon.MEDIA_JSON, 'application/json'):
        if not req.content_length:
            raise RPCError(errors.MISSING_BODY)
        else:
            try:
                req.context['data'] = json.load(req.bounded_stream)
            except json.JSONDecodeError:
                raise RPCError(errors.BAD_JSON)
    elif (req.content_type and
          'application/x-www-form-urlencoded' in req.content_type and
          req.content_length):
        body = req.bounded_stream.read(req.content_length).decode()
        req.context[URL_ENCODED] = copy.deepcopy(body)
        req.context['data'] = falcon.uri.parse_query_string(body)
    else:
        req.context['data'] = req.params


def _get_get_data(req, resp, resource, params):
    """Load our GET query params to the context object
    """
    req.context['data'] = req.params


class RPC:
    """The main class that we init and use to launch
    the API. This wraps the normal ``falcon.API`` object
    and sets up our single route handler and provides
    an interface to attach method handlers """

    def __init__(self):
        """Create the default Falcon API"""
        self.router = RPCRouter()
        cors = CORS(
            allow_all_origins=True,
            allow_all_headers=True,
            allow_all_methods=True
        )
        self.falcon = falcon.API(
            middleware=[cors.middleware, RPCResponseInterceptor()])
        # NOTE(jtm): we manually do this so we can preserve
        # the original url encoded string if needed
        self.falcon.req_options.auto_parse_form_urlencoded = False
        self.falcon.add_route('/{method}', self.router)
        self.falcon.set_error_serializer(_json_error_serializer)

    def add_family(self, family_inst):
        f_name = family_inst.__class__.__name__.lower()
        self.router.families[f_name] = family_inst

    def __call__(self):
        return self.falcon


class RPCRequest:
    """Representation of an HTTP RPC request

    This will contain information such as
    the parsed payload params and the original
    Falcon HTTP Request so all that information
    is available to the RPC handlers.
    """

    __slots__ = (
        'params',
        'urlencoded_string',
        'req',
        'resp_body',
        'warning'
    )

    def __init__(self, params, req: falcon.Request):
        """Create a RPC Request

        An instance of this object will be passed
        to all handlers. Handlers may use any
        of the attributes in their logic and
        ``resp_body`` will be used by Falcon
        as the return value to the caller.

        Attributes:
            params (dict): parse GET params or POST body params
            req (Request): original Falcon Request object
            resp_body (dict): the response that will be sent
                to the caller. Will be serialized to JSON
                via middleware
            warning (str): an optional warning that can be
                set when returning data to the caller
        """
        self.params = params
        self.req = req
        self.resp_body = None
        self.warning = None
        self.urlencoded_string = None

        # save off our original x-www-form-urlencoded string
        try:
            self.urlencoded_string = self.req.context[URL_ENCODED]
        except KeyError:
            pass

    def _fini(self):
        if not self.resp_body:
            self.resp_body = {}

        if self.warning:
            self.resp_body['warning'] = self.warning

    def get_header(self, name, default=None):
        return self.req.get_header(name, default=default)

    def set_warning(self, warning):
        """Set a warning message that will
        be added to the response body just
        before returning to the caller
        """
        self.warning = warning


class RPCRouter:
    """We only use a single Falcon Resource
    to handle all requests. Since we are using
    a ``METHOD_FAMILY.method`` for our RPC calls
    we can just pass the single ``method`` param
    that Falcon parses to some API-agnostic
    handler. """

    def __init__(self):
        self.families = {}

    @falcon.before(_get_get_data)
    def on_get(self, req, resp, method):
        self.handle_request(req, resp, method)

    @falcon.before(_get_post_data)
    def on_post(self, req, resp, method):
        self.handle_request(req, resp, method)

    def handle_request(self, req, resp, method):
        """Handle HTTP request """
        try:
            f_name, method = method.split('.')
        except ValueError:
            raise RPCError(errors.BAD_METHOD)

        if method.startswith('_'):
            raise RPCError(errors.BAD_METHOD)

        try:
            family_inst = self.families[f_name.lower()]
        except KeyError:
            raise RPCError(errors.UNK_FAMILY)

        try:
            worker = getattr(family_inst, method)
        except AttributeError:
            raise RPCError(errors.UNK_METHOD)

        rpc_req = RPCRequest(
            req.context['data'],
            req
        )

        try:
            worker(rpc_req)
            rpc_req._fini()
            resp.body = rpc_req.resp_body
        except Exception as e:
            # check if we actually raised RPCError
            if e.__class__.__name__ == RPCError.__name__:
                raise
            if e.__class__.__name__ == RPCRedirect.__name__:  # pragma: no cover  # noqa
                raise
            else:
                logger.exception('Unhandled exception!')
                raise RPCError(errors.FATAL)


class RPCError(falcon.HTTPError):
    """Overload Falcon's top-level HTTP
    Error handler so we can force a 200 OK
    for every error response and then
    set the custom `ok` and `error` fields
    in the response body """

    def __init__(self, err_string=None):
        self.err_string = err_string
        # we always provide a 200 OK
        super().__init__(falcon.HTTP_200)

    def to_dict(self, obj_type=dict):
        """Overload Falcon's ``to_dict`` method
        to set the `ok` param and set the custom
        error code """

        obj = obj_type()
        obj['ok'] = False
        obj['error'] = self.err_string
        return obj


class RPCRedirect(falcon.HTTPFound):
    """Overload Falcon's HTTPFound
    so we can support redirects from
    RPC calls
    """
    pass


class RPCResponseInterceptor:

    def process_response(self, req, resp, resource, req_succeeded):
        if req_succeeded:
            resp.body['ok'] = True

        # this runs for errors, too
        resp.body = json.dumps(resp.body)
        resp.media = falcon.MEDIA_JSON
