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

    def __init__(self, address, loop, 
            request_cb, response_cb, error_cb, connect_cb=None):
        self.request_cb = request_cb
        self.response_cb = response_cb
        self.error_cb = error_cb
        self.connect_cb = connect_cb
        self.last_qps = 0    
        self.current_qps = 0
        self.sock = None
        self.watcher = None
        self.address = address
        self.buf = ''
        self.read_buf = ''
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
            if not self.connect_cb:
                self.connect_cb = self.io_cb 
            self.state = Connection.STATE_CONNECTING
            self.watcher = pyev.Io(
                    self.sock, 
                    pyev.EV_WRITE, 
                    self.loop, 
                    self.connect_cb)
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
            self.error_cb(self)
        self.state = Connection.STATE_ERROR
        
    def handle_read(self):
        try:
            logging.debug('handling read')
            self.read_buf += self.sock.recv(1024)
            logging.debug('reading %s' % self.read_buf)
        except socket.error as err:
            if err.args[0] not in NONBLOCKING:
                self.handle_error("error reading from {0}".format(self.sock))
        if self.read_buf:
            buf = self.response_cb(self.read_buf)
            # was it a full response ?           
            if not buf :
                # we got a full response                
                self.current_qps += 1
                self.read_buf = ''
                self.reset(pyev.EV_WRITE)
            else : 
                # we got a partial response keep on reading
                logging.debug('partial buffer received %s' % self.read_buf)
                self.read_buf += buf
                self.reset(pyev.EV_READ)
        else:
            self.handle_error("connection closed by peer", logging.DEBUG, False)

    def handle_write(self):
        try:
            logging.debug('handling write')
            if not self.buf :
                self.buf += self.request_cb()            
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
                # all the request buffer was sent, 
                # let's wait for the response
                self.reset(pyev.EV_READ)
            else :
                # there is still some buffer left, 
                # wait for the write event again
                logging.info('partial buffer sent')
                self.reset(pyev.EV_WRITE)

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


