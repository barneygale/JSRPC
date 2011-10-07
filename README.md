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
    js.http_root = 'web'
    js.start()
    
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

## Notes on variable access
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

## Webserver
The default webserver serves files from a specific folder. You can set your HTTP root location thusly:
    js.http_root = 'public_html'
You can also substitute in your own request handler. Do it like this:
    class MyRequestHandler(jsrpc.request_handler):
        def _do_GET(self):
            ...
        def _do_POST(self):
            ...
    jsrpc.request_handler = MyRequestHandler()
Note that the jsrpc.request_handler is almost identical to BaseHTTPRequestHandler, so base your
extension on that. You get passed every HTTP request that isn't part of the RPC stuff.
