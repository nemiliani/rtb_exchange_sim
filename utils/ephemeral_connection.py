import pyev
import os
import sys
import logging
import socket
import signal
import errno

NONBLOCKING = (errno.EAGAIN, errno.EWOULDBLOCK)

class EphemeralConnection(object):
    '''
        The connection is meant to send a buffer,
        receive a response and be closed
    '''
    STATE_NOT_CONNECTED = 'CONNECTED'
    STATE_CONNECTING = 'CONNECTING'
    STATE_CONNECTED = 'NOT_CONNECTED'
    STATE_ERROR = 'ERROR'
    STATE_IDLE = 'IDLE'
    _id = 1

    def __init__(self, loop, address, buf, response_cb, 
                    error_cb, no_response_cb, connect_cb=None):
        self.loop = loop
        self.address = address
        self.buf = buf
        self.read_buf = ''
        self.response_cb = response_cb
        self.error_cb = error_cb
        self.no_response_cb = no_response_cb
        self.connect_cb = connect_cb
        self.sock = None
        self.timer = None
        self.watcher = None
        self.id = EphemeralConnection._id
        EphemeralConnection._id += 1

    def __del__(self):
        logging.info('------------------> ad __del__ conn %d' % self.id)
        pass

    def connect(self):
        '''
            Connect and set the app layer timeout
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logging.debug('EphemeralConnection : connecting to %s:%d' %
                            (self.address[0], self.address[1]))
        res = self.sock.connect_ex(self.address)
        if res != errno.EINPROGRESS :
            logging.error('EphemeralConnection : unable to connect to %s:%d res=%d' %
                            (self.address[0], self.address[1], res))
            self.state = EphemeralConnection.STATE_ERROR
            self.handle_error('unable to connect')
        else:
            if not self.connect_cb:
                self.connect_cb = self.io_cb 
            self.state = EphemeralConnection.STATE_CONNECTING
            self.watcher = pyev.Io(
                    self.sock, 
                    pyev.EV_WRITE, 
                    self.loop, 
                    self.connect_cb)
            self.watcher.start()
            # start the application layer time out
            self.timer = pyev.Timer(2, 0.0, self.loop, self.no_response_cb)
            self.timer.start()
        return self.state

    def reset(self, events):
        self.watcher.stop()
        self.watcher.set(self.sock, events)
        self.watcher.start()

    def handle_error(self, msg, level=logging.ERROR, exc_info=True):
        logging.error("{0}: {1} --> closing".format(self, msg),
                             exc_info=exc_info)
        self.close()
        self.error_cb(self)
        self.state = EphemeralConnection.STATE_ERROR

    def handle_read(self):
        try:
            logging.debug('EphemeralConnection : handling read %d' % self.id)
            self.read_buf += self.sock.recv(1024)
            logging.debug('EphemeralConnection : reading %s' % self.read_buf)
        except socket.error as err:
            if err.args[0] not in NONBLOCKING:
                self.handle_error("error reading from {0}".format(self.sock))
            else :
                logging.error('NONBLOCKING event on read')
        if self.read_buf:
            buf = self.response_cb(self.read_buf, self)
            # was it a full response ?           
            if buf : 
                # we got a partial response keep on reading
                logging.debug('partial buffer received %s' % self.read_buf)
                self.read_buf += buf
                self.reset(pyev.EV_READ)
        else:
            self.handle_error(
                "connection closed by peer", logging.DEBUG, False)    

    def handle_write(self):
        try:
            logging.debug('EphemeralConnection : handling write %d' % self.id)
            self.state = EphemeralConnection.STATE_CONNECTED         
            logging.debug('EphemeralConnection : sending %s' % self.buf)
            sent = self.sock.send(self.buf)
        except socket.error as err:
            logging.error('EphemeralConnection : handle_write ex')            
            if err.args[0] not in NONBLOCKING:
                self.handle_error(
                    "EphemeralConnection : error writing to {0}".format(
                     self.sock))
            else :
                logging.error(
                    'EphemeralConnection : NONBLOCKING event on write')
        else :
            if self.state == EphemeralConnection.STATE_CONNECTING:
                self.state = EphemeralConnection.STATE_CONNECTED
            self.buf = self.buf[sent:]
            if not self.buf:
                # all the request buffer was sent, 
                # let's wait for the response
                self.reset(pyev.EV_READ)
            else :
                # there is still some buffer left, 
                # wait for the write event again
                logging.info('EphemeralConnection : partial buffer sent')
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
        self.sock = None
        logging.debug("EphemeralConnection : closed %d" % self.id)
