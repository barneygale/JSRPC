# JSRPC
JSRPC _(javascript remote procedure call)_ is a small library for those wishing to write python
applications with web interfaces. the JSRPC class creates a small HTTP server, through which AJAX
requests can be exchanged.

The project consists of two parts:

1. A python library providing a JSRPC() object, through which javascript calls can be made
2. A small jQuery plugin to handle these calls

## Usage
in python:

    import jsrpc
    
    js = jsrpc.JSRPC()
    
    #For example:
    print "window.location.href: %s" % js.sync.window.location.href
    print "window.prompt(): %s" % js.sync.window.prompt('What is your name?')

in javascript:

    <script src="jquery-1.6.4.js"></script>
    <script src="jquery-json-2.3.js"></script>
    <script src="jquery-jsrpc.js"></script>
    <script>
    $(document).ready(function() {
        $.jsrpc_start();
    });
    
    </script>

## Sync and Async
synchronous calls wait for javascript to return a value. They take the form:

    js.sync.window.prompt('Why are you here?')

asynchronous calls won't block, and will call a specified callback function with the value.

    def callback(text):
        print text
    js.async(callback).window.prompt('Why are you here?')

if you don't care about return values, you can cast into the void:

    js.async.window.alert('To see with eyes unclouded by hate.')

## Limitations

### Data format
You can only pass around data that can be encoded as JSON. numbers, arrays, dicts, strings, etc
are all fine, but you won't get anything back from js.sync.document.getElementById('blah'), and
you can forget about most objects.

### Variable access
When accessing variables in async mode, you will _always_ needs to call .flush(). For example:

    def callback(location):
        print location
    js.async(callback).window.location.href.flush()

This is also _sometimes_ true for variables in sync mode. Most of the time it will work, but you
may run into situation when it won't.

## Messages
Sometimes you want to alert your python program of something from javascript, outside of a return
value. For this, you can use messages. First assign a message handler in python:

    def get_message(message):
        print "got a message:", message
    js.message_handler = get_message

You can then send messages (with an arbitary data format) to python from javascript:

    <input type="text" id="text" />
    <input type="submit" id="send" value="send" />

...

    $(document).ready(function() {
        $.jsrpc_start();
        $('#send').click(function() {
            $.jsrpc_message($('#text').val());
        });
    });

## Webserver options
JSRPC packages a basic webserver based on BaseHTTPServer.HTTPServer. You can pass options to JSRPC():

* `server` specifies a server object. It is passed the `jsrpc.io` method, and any kargs, in its constructor
* if `server` isn't specified, you can configure the default server:
	* `interface`: the interface to listen on (defaults to '')
	* `port`: defaults to 8080
	* `http_root`: directory to serve files from
	* `request_handler`: subclass of BaseHTTPRequestHandler. Defaults to webserver.JSRPCRequestHandler.

Subclassing JSRPCRequestHandler is useful for handling GET and POST yourself

    class MyRequestHandler(webserver.JSRPCRequestHandler):
        def _do_GET(self):
            ...
        def _do_POST(self):
            ...

    js = jsrpc.JSRPC(request_handler = MyRequestHandler)

Note that the jsrpc.RequestHandler is almost identical to BaseHTTPRequestHandler, so 
base your extension on that. You get passed every HTTP request that isn't part of the RPC stuff.
