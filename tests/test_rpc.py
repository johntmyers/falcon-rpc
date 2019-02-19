import json

import pytest

from falcon import testing
import falcon_rpc


class Test:

    def echo(self, req):
        req.resp_body = {'you_said': req.params}

    def camelCall(self, req):
        req.resp_body = {'camel': 'hump day'}

    def error(self, req):
        raise falcon_rpc.RPCError('much_error')

    def fatal(self, req):
        raise TypeError('oops')

    def do_nothing(self, req):
        return

    def warn(self, req):
        req.set_warning('some_warning')
        req.resp_body = {'stuff': 'mostly good'}

    def warn_error(self, req):
        req.set_warning('does_not_matter')
        raise falcon_rpc.RPCError('another_error')


# test API
def create():
    rpc = falcon_rpc.RPC()
    rpc.add_family(Test())
    return rpc()


@pytest.fixture(scope='module')
def client():
    return testing.TestClient(create())


def test_get_no_params(client):
    check = {'ok': True, 'you_said': {}}
    assert client.simulate_get('/test.echo').json == check


def test_get_no_params_case(client):
    check = {'ok': True, 'you_said': {}}
    assert client.simulate_get('/Test.echo').json == check


def test_get_params(client):
    check = {'ok': True, 'you_said': {'foo': 'bar', 'stuff': 'junk'}}
    assert client.simulate_get(
        '/test.echo', query_string='foo=bar&stuff=junk').json == check


def test_bad_method_str(client):
    check = {'ok': False, 'error': falcon_rpc.BAD_METHOD}
    assert client.simulate_get('/bad_call').json == check
    assert client.simulate_get('/too.many.dots').json == check


def test_get_family_dne(client):
    check = {'ok': False, 'error': falcon_rpc.UNK_FAMILY}
    assert client.simulate_get('/big.nope').json == check


def test_get_method_dne(client):
    check = {'ok': False, 'error': falcon_rpc.UNK_METHOD}
    assert client.simulate_post('/test.dne').json == check


def test_get_method_dne_case(client):
    check = {'ok': False, 'error': falcon_rpc.UNK_METHOD}
    assert client.simulate_get('/test.Echo').json == check


def test_camel_case_method(client):
    check = {'ok': True, 'camel': 'hump day'}
    assert client.simulate_post('/test.camelCall').json == check


def test_get_error(client):
    check = {'ok': False, 'error': 'much_error'}
    assert client.simulate_get('/test.error').json == check


def test_post_no_params(client):
    check = {'ok': True, 'you_said': {}}
    assert client.simulate_post('/test.echo').json == check


def test_post_json_body(client):
    payload = {'foo': 'bar', 'stuff': 'junk'}
    check = {'ok': True, 'you_said': payload}
    assert client.simulate_post(
        '/test.echo',
        headers={'Content-Type': 'application/json'},
        body=json.dumps(payload)
        ).json == check


def test_post_form_body(client):
    payload = {'foo': 'bar', 'stuff': 'junk'}
    check = {'ok': True, 'you_said': payload}
    assert client.simulate_post(
        '/test.echo',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        body='foo=bar&stuff=junk'
        ).json == check


def test_post_json_no_body(client):
    check = {'ok': False, 'error': falcon_rpc.MISSING_BODY}
    assert client.simulate_post(
        '/test.echo',
        headers={'Content-Type': 'application/json'}
    ).json == check


def test_post_json_bad_body(client):
    check = {'ok': False, 'error': falcon_rpc.BAD_JSON}
    assert client.simulate_post(
        '/test.echo',
        headers={'Content-Type': 'application/json'},
        body='nope'
    ).json == check


def test_post_fatal(client):
    check = {'ok': False, 'error': falcon_rpc.FATAL}
    assert client.simulate_post(
        '/test.fatal'
    ).json == check


def test_get_fatal(client):
    check = {'ok': False, 'error': falcon_rpc.FATAL}
    assert client.simulate_get(
        '/test.fatal'
    ).json == check


def test_no_resp_body(client):
    check = {'ok': True}
    assert client.simulate_get('/test.do_nothing').json == check


def test_ok_with_warning(client):
    check = {'ok': True, 'stuff': 'mostly good', 'warning': 'some_warning'}
    assert client.simulate_post('/test.warn').json == check


def test_error_with_warning(client):
    check = {'ok': False, 'error': 'another_error'}
    assert client.simulate_get('/test.warn_error').json == check
