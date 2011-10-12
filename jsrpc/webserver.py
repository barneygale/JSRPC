import glob
import os

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import threading

class JSRPCServer(HTTPServer, threading.Thread):
    def __init__(self, io, **kargs):
        self.io = io
        
        self.config = {'interface': '', 'port': 8080, 'handler': JSRPCRequestHandler, 'http_root': ''}
        self.config.update(kargs) 
        
        #Javascript includes
        self.include_path = os.path.dirname(os.path.realpath(__file__))
        self.js_includes = []
        for js in glob.glob(os.path.join(self.include_path, '*.js')):
            self.js_includes.append(os.path.basename(js))
        
        #Init
        HTTPServer.__init__(self, (self.config['interface'], self.config['port']), self.config['handler'])    
        threading.Thread.__init__(self)

    def run(self):
        self.serve_forever()
class JSRPCRequestHandler(BaseHTTPRequestHandler):    
    def log_message(self, *args):
        pass

    def do_GET(self):
        basename = os.path.basename(self.path) 
        if basename in self.server.js_includes:
            f = open(os.path.join(self.server.include_path, basename))
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        else:
            return self._do_GET()

    def do_POST(self):
        if self.path == '/ajax.cgi':
            #Decode the data
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
            
            #Return the return_values
            #Build and encode write array
            read_buff = postvars['array'][0]
            write_buff = self.server.io(read_buff)
            
            #Send data
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(write_buff)
        else:
            return self._do_POST()

    def _do_GET(self):
        if self.path.strip('/') == '':
            self.path = '/index.html'
        self.path = self.server.config['http_root'] + self.path
        
        try:
            f = open(self.path)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
        return

    def _do_POST(self):
        self._do_get()
