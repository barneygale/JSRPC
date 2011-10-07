import os
import re
import json

import multiprocessing
import threading
import Queue

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

class JSRPC(HTTPServer, threading.Thread):
	def __init__(self, **kargs):
		if 'request_handler' in kargs:
			request_handler = kargs['request_handler']
		else:	request_handler = RequestHandler

		self.http_root = ''
		self.sync =  SyncRootNode('sync',  self, SyncNode)
		self.async= AsyncRootNode('async', self, AsyncNode)
		self.message_handler = lambda message: 0
		
		#Counter: used to give messages IDs
		self.counter = 0
		self.counter_lock = multiprocessing.Lock()
		
		#Message buffer: records messages waiting for a return
		self.message_buffer = {}
		self.message_buffer_lock = multiprocessing.Lock()
		
		#Message queue: messages to be written to the socket
		self.message_queue = Queue.Queue()
		
		HTTPServer.__init__(self, ('', 8080), request_handler)
		threading.Thread.__init__(self)
	#Get a new ID from the counter
	def get_id(self):
		with self.counter_lock:
			self.counter += 1
			j = self.counter
		return j

	def pass_down(self, node, data):
		data['path'] = data['path'][1:] #Pop sync/async off the path
		id = self.get_id()
		#Add to message buffer
		with self.message_buffer_lock:
			self.message_buffer[id] = node
		#Send the ID with the message
		data['id'] = id
		#Put it on the message queue
		self.message_queue.put(data)
	
	def run(self):
		self.serve_forever()
class RequestHandler(BaseHTTPRequestHandler):	
	def log_message(self, *args):
		pass
	def do_GET(self):
		return self._do_GET()
	def do_POST(self):
		if self.path == '/ajax.cgi':
			#Decode the data
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			length = int(self.headers.getheader('content-length'))
			postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
			messages = json.loads(postvars['array'][0])
			#Return the return_values
			with self.server.message_buffer_lock:
				for m in messages:
					if m['type'] == 'message':
						self.server.message_handler(m['value'])
					if m['type'] == 'fn':
						try:
							self.server.message_buffer[m['id']].get_return(m['value'])
							del self.server.message_buffer[m['id']]
						except: pass # <-- awesome error handling
			
			#Build and encode write array
			write = []
			try:
				while True:
					write.append(self.server.message_queue.get_nowait())
			except Queue.Empty: pass
			write = json.dumps(write)
			
			#Send data
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write(write)
		else:
			return self._do_POST()
	def _do_GET(self):
		if self.path.strip('/') == '':
			self.path = '/index.html'
		self.path = self.server.http_root + self.path
		
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
class Node:
	def __init__(self, name, parent, ty, **setup):
		self.parent = parent
		self.name = name
		self.ty = ty
		self.return_value = None
		self.setup = setup
	
	def __getattr__(self, name):
		m = re.match('^__.*__$', name)
		#System attribute (__foo__): interpret as python
		if m: return getattr(self.flush(), name)
		#None system call: interpret as javascript
		else: return self.ty(name, self, self.ty, **self.setup)
	
	#Special case: function call
	def __call__(self, *args):
		return self.execute({'type':'fn', 'args':list(args)})
	
	#Insert current node's name to path and pass to parent
	def pass_down(self, node, data):
		data["path"].insert(0, self.name)
		return self.parent.pass_down(node, data)
	
	#Force the current node to be evaluated
	def flush(self):
		if self.return_value == None:
			self.return_value = self.execute({'type':'nofn'})
		return self.return_value

class SyncNode(Node):
	def __init__(self, name, parent, ty, **setup):
		Node.__init__(self, name, parent, ty, **setup)
		self.lock = multiprocessing.Lock()

	def execute(self, data):
		data["path"] = []
		#Send the request
		self.lock.acquire()
		self.pass_down(self, data)
		#Wait for a reply (i.e. the lock to be released)
		self.lock.acquire()
		self.lock.release()
		return self.return_value_temp

	def get_return(self, value):
		self.return_value_temp = value
		self.lock.release()
		

class AsyncNode(Node):
	def __init__(self, name, parent, ty, **setup):
		Node.__init__(self, name, parent, ty, **setup)
		if 'callback' in setup:
			self.callback = setup['callback']
		else:   self.callback = None

	def execute(self, data):
		data["path"] = []
		self.pass_down(self, data)
		return None

	def get_return(self, value):
		if self.callback:
			self.callback(value)

class SyncRootNode(Node):
	pass
class AsyncRootNode(Node):
	def __call__(self, *args):
		if args: kargs={'callback': args[0]}
		else:    kargs={}
		return AsyncRootNode('async', self.parent, AsyncNode, **kargs)
