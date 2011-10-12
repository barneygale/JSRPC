#!/usr/bin/python
import jsrpc
import time

try:
    def get_message(message):
        print "    -> got a message: %s" % message

    js = jsrpc.JSRPC(port=8080, http_root='demo_www')

    print "### Testing synchronous"
    print "# Variable access"
    print "    -> window.location.href: %s" % js.sync.window.location.href
    print "# Function call"
    print "    -> window.prompt(): %s" % js.sync.window.prompt('Enter some data...')


    def location(value):
        print "    -> window.location.href: %s" % value

    def prompt(value):
        print "    -> window.prompt(): %s" % value


    print "### Testing asynchronous"
    print "# Variable access"
    js.async(location).window.location.href.flush() #Note that flush() is necessary for async variable access
    print "# Function call"
    js.async(prompt).window.prompt('Enter some data...')

    print "### Testing asynchronous no-return"
    print "# Variable access (lulwut)"
    js.async.window.location.href.flush()
    print "# Function call"
    js.async.window.prompt('Enter some data...')
    time.sleep(10000)
except Exception, e:
    js.server.shutdown()
