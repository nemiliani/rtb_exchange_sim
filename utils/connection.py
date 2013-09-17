import pyev
import os
import sys
import logging
import socket
import signal
import errno
import weakref



class Connection(object):
    '''
        Client connection to an rtb server
    '''
    
    STATE_NOT_CONNECTED = 'CONNECTED'
    STATE_CONNECTED = 'NOT_CONNECTED'
    STATE_ERROR = 'ERROR'

    def __init__(self, address, loop):
        self.current_qps = 0
        self.sock = None
        self.address = address
        self.buf = ''
        self.state = Connection.STATE_NOT_CONNECTED
        logging.debug("{0}: ready".format(self))

    def connect(self):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setblocking(0)
#        try:
            logging.debug('connecting to %s:%d' %
                            (self.address[0], self.address[1]))
            self.sock.connect(('localhost',9876))
            self.state = Connection.STATE_CONNECTED
#        except :
            logging.error('unable to connect to %s:%d' %  
                            (self.address[0], self.address[1]))
            self.state = Connection.STATE_ERROR

    def reset(self, events):
        self.watcher.stop()
        self.watcher.set(self.sock, events)
        self.watcher.start()

    def handle_error(self, msg, level=logging.ERROR, exc_info=True):
        logging.log(level, "{0}: {1} --> closing".format(self, msg),
                    exc_info=exc_info)
        self.close()
        self.ok = False

    def handle_read(self):
        try:
            buf = self.sock.recv(1024)
        except socket.error as err:
            if err.args[0] not in NONBLOCKING:
                self.handle_error("error reading from {0}".format(self.sock))
        if buf:
            self.buf += buf
            self.reset(pyev.EV_READ | pyev.EV_WRITE)
        else:
            self.handle_error("connection closed by peer", logging.DEBUG, False)

    def handle_write(self):
        try:
            sent = self.sock.send(self.buf)
        except socket.error as err:
            if err.args[0] not in NONBLOCKING:
                self.handle_error("error writing to {0}".format(self.sock))
        else :
            self.buf = self.buf[sent:]
            if not self.buf:
                self.reset(pyev.EV_READ)

    def io_cb(self, watcher, revents):
        if revents & pyev.EV_READ:
            self.handle_read()
        else:
            self.handle_write()

    def close(self):
        self.sock.close()
        self.watcher.stop()
        self.watcher = None
        logging.debug("{0}: closed".format(self))


