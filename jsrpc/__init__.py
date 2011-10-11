import re
import json

import multiprocessing
import Queue

import webserver

class JSRPC:
	def __init__(self, **kargs):
		#Webserver
		if 'server' in kargs:
			self.server = kargs['server']
		else:
			self.server = webserver.JSRPCServer(self.io, **kargs)
			self.server.start()
		#.sync and .async
		self.sync =  SyncRootNode('sync',  self,  SyncNode)
		self.async= AsyncRootNode('async', self, AsyncNode)
		
		#do-nothing message handler
		self.message_handler = lambda message: 0
		
		#Counter: used to give messages IDs
		self.counter = 0
		self.counter_lock = multiprocessing.Lock()
		
		#Message buffer: records messages waiting for a return
		self.message_buffer = {}
		self.message_buffer_lock = multiprocessing.Lock()
		
		#Message queue: messages to be written to the socket
		self.message_queue = Queue.Queue()
		
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
	
	#1. Write return values to handlers
	#2. Read from message queue
	def io(self, read):
		#Read
		read = json.loads(read)
		with self.message_buffer_lock:
			for m in read:
				if m['type'] == 'message':
					self.message_handler(m['value'])
				if m['type'] == 'fn':
					try:
						self.message_buffer[m['id']].get_return(m['value'])
						del self.message_buffer[m['id']]
					except: pass # <-- awesome error handling
		#Write
		write = []
		try:
			while True:
				write.append(self.message_queue.get_nowait())
		except Queue.Empty: pass
		return json.dumps(write)
		
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
