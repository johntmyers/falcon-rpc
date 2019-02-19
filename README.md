# Falcon RPC

## Background

A wrapper that utilizes the [Falcon Framework](https://falconframework.org/) to create a HTTP RPC API.

The motivation for this API is the [Slack Web API](https://api.slack.com/web). 

*NOTE*: I suggest being familiar with Falcon and Slack's APIs on your own, first.

I found myself creating lots of APIs for various projects and realized that RESTful APIs are not really useful for the type of stuff I work on.  While there is a certain degree of CRUD operations I usually need to do, a lot of the "resources" I created were for kicking of backend processing jobs, running async analytic workloads, executing complex queries, etc.

Most of the things I do just don't fit into REST. Frankly, instead of "bending" REST to fit my will I found API's like Slack that seemed perfect for being flexible enough to fit any use case. However, while I was bending REST for my bidding I became really fond of the Falcon Framework. I 100% understand Falcon is designed for REST but guess what, I can do whatever I want so here we are. 

## Quickstart

Clone the repo and install.

```
cd falcon_rpc
pip install -I .
``` 

```python
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


class Another:

    def show_me(self, req):
        # req.req is the original Falcon Request object
        req.resp_body = {'hello_there': req.req.remote_addr}


def start():
    rpc = falcon_rpc.RPC()
    rpc.add_family(Test())
    rpc.add_family(Another())
    return rpc()
```

This can be launched just like you would Falcon:

```
$ gunicorn -b :8000 "app:start()" --workers 2 --log-level DEBUG --reload
```

## Method Families and Methods

Instead of adding routes to your API, you add method families, which are Python classes here.

Your API follows the `/METHOD_FAMILY.method` structure like Slack and the name of your Python class corresponds to the method family, and methods of that class are utilized as the actual method being called.

It is important to note that method family names are case insensitive, they will always be cast to lowercase.

Method names are case sensitive.

### Method Handlers

Method handlers take one arg, an instance of `RPCRequest`.

The `resp_body` attribute of this object can be set with your response data.

Like Slack, if your request could be processed, but you need to add a warning, you can do so by using the `set_warning` method.

## Tests

```
$ pip install -r test-requirements.txt
$ pytest -s -vv --cov falcon_rpc --cov-report=term-missing tests/
```