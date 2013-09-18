import pyev
import os
import sys
import logging
import socket
import signal
import errno
import weakref

NONBLOCKING = (errno.EAGAIN, errno.EWOULDBLOCK)

class Connection(object):
    '''
        Client connection to an rtb server
    '''
    
    STATE_NOT_CONNECTED = 'CONNECTED'
    STATE_CONNECTING = 'CONNECTING'
    STATE_CONNECTED = 'NOT_CONNECTED'
    STATE_ERROR = 'ERROR'
    
    _id = 1

    def __init__(self, exchange, address, loop):
        self.exchange = exchange
        self.last_qps = 0    
        self.current_qps = 0
        self.sock = None
        self.watcher = None
        self.address = address
        self.count = 0
        self.buf = 'Hola_%d' % self.count
        self.state = Connection.STATE_NOT_CONNECTED
        self.loop = loop
        self.id = Connection._id
        Connection._id += 1
        logging.debug("{0}: ready".format(self))

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        logging.debug('connecting to %s:%d' %
                            (self.address[0], self.address[1]))
        res = self.sock.connect_ex(self.address)
        if res != errno.EINPROGRESS :
            logging.error('unable to connect to %s:%d' %  
                            (self.address[0], self.address[1]))
            self.state = Connection.STATE_ERROR
        else:
            self.state = Connection.STATE_CONNECTING
            self.watcher = pyev.Io(
                    self.sock, 
                    pyev.EV_WRITE, 
                    self.loop, 
                    self.io_cb)
            self.watcher.start()
            # start the timer
            self.timer = pyev.Timer(1, 1, self.loop, self.set_qps)
            self.timer.start()
        return self.state

    def set_qps(self, watcher, revents):
        self.last_qps = self.current_qps
        self.current_qps = 0        

    def reset(self, events):
        self.watcher.stop()
        self.watcher.set(self.sock, events)
        self.watcher.start()

    def handle_error(self, msg, level=logging.ERROR, exc_info=True):
        logging.error("{0}: {1} --> closing".format(self, msg),
                             exc_info=exc_info)
        self.close()
        if self.state != Connection.STATE_CONNECTING:    
            self.exchange.remove_connection(self)
        self.state = Connection.STATE_ERROR
        
    def handle_read(self):
        try:
            buf = self.sock.recv(1024)
            logging.debug('reading %s' % buf)
        except socket.error as err:
            if err.args[0] not in NONBLOCKING:
                self.handle_error("error reading from {0}".format(self.sock))
        if buf:
            self.current_qps += 1
            self.reset(pyev.EV_WRITE)
        else:
            self.handle_error("connection closed by peer", logging.DEBUG, False)

    def handle_write(self):
        try:
            logging.debug('sending %s' % self.buf)
            sent = self.sock.send(self.buf)
        except socket.error as err:
            logging.error('handle_write ex')            
            if err.args[0] not in NONBLOCKING:
                self.handle_error("error writing to {0}".format(self.sock))
        else :
            if self.state == Connection.STATE_CONNECTING:
                self.state = Connection.STATE_CONNECTED
            self.buf = self.buf[sent:]
            if not self.buf:
                self.buf = 'Hola_%d' % self.count                
                self.count += 1
                self.reset(pyev.EV_READ)

    def io_cb(self, watcher, revents):
        if revents & pyev.EV_READ:
            self.handle_read()
        else:
            self.handle_write()

    def close(self):
        self.sock.close()
        if self.watcher :
            self.watcher.stop()
            self.watcher = None
            self.timer.stop()
            self.timer = None
        logging.debug("{0}: closed".format(self))


