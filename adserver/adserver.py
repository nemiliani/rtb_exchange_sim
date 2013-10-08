import pyev
import os
import sys
import logging
import socket
import signal
import errno

from settings import  EVENT_ENDPOINT
from utils import Connection

class AdConnection(object):

    def __init__(self, loop, endpoint, buf):
        pass

    def connect(self):
        pass

    def send_buffer(self, buf):
        pass

    def reset(self, events):
        pass

    def handle_error(self, msg, level=logging.ERROR, exc_info=True):
        pass

    def handle_read(self):
        pass    

    def handle_write(self):
        pass

    def io_cb(self):
        pass

class AdServer(object):

    def __init__(self, loop):
        self.loop = loop
        self.watchers = []
        ep = EVENT_ENDPOINT.split(':')
        self.endpoint = (ep[0], int(ep[1]))
        self.conns = []

    def send_event(self, buf, timeout):
        # set the timeout to call the method that will
        # create the connection and send the buffer (send buffer)
        pass

    def send_http(self, buf):
        # create the ad connection, set the buff
        # and recv_http callback and the connect to send it
        pass
       
    def recv_http(self, conn):
        # receive the response, maybe pint the status code,
        # close the connection and erase it form the list
        pass
