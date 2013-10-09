import pyev
import os
import sys
import logging
import socket
import signal
import errno
import random
import weakref

from settings import  EVENT_ENDPOINT
from utils import EphemeralConnection

class AdServer(object):

    def __init__(self, loop):
        self.loop = loop
        self.watchers = []
        ep = EVENT_ENDPOINT.split(':')
        self.endpoint = (ep[0], int(ep[1]))
        self.timers = []
        self.stats_timer = pyev.Timer(
                            3.0, 
                            3.0, 
                            self.loop,
                            self.print_stats)
        self.stats_timer.start()
        self.reqs = 0
        self.resps = 0
        self.no_resps = 0
        self.errors = 0

    def stop(self):
        self.stats_timer.stop()
        for v in self.timers:
            v.stop()
        logging.debug("{0}: stopped".format(self))

    def print_stats(self, watcher, revents):
        logging.info(
            'evs=%d reps=%d errs=%d noresps=%d, endpoint=%s:%d' % 
            (self.reqs, self.resps, self.errors, self.no_resps, 
            self.endpoint[0], self.endpoint[1]))

    def send_event(self, buf, timeout):
        # set the timeout to call the method that will
        # create the connection and send the buffer (send buffer)
        logging.debug('ad.send_event creating conn')

        conn = EphemeralConnection(
                self.loop, self.endpoint, buf, self.recv_http, 
                self.on_error, self.no_response)
        to = pyev.Timer(
                            timeout, 
                            0.0, 
                            self.loop, 
                            self.send_http,
                            conn)
        to.start()
        self.timers.append(to)
        logging.debug('ad.send_event creating conn done %d' % conn.id)

    def send_http(self, watcher, revents):
        # create the ad connection, set the buff
        # and recv_http callback and the connect to send it
        conn_id = watcher.data.id
        logging.debug('ad.send_http %d' % conn_id)
        try:
            logging.debug('ad.send_http connecting')
            watcher.data.connect()
            logging.debug('ad.send_http connecting done')
            self.reqs += 1
        except KeyError :
            logging.error('AdServer : no conn %d found' % conn_id)
        except :
            logging.error('AdServer : error sending http')
        self.timers.remove(watcher)
        logging.debug('ad.send_http done')

       
    def recv_http(self, buf, conn):
        # receive the response, maybe pint the status code,
        # close the connection and erase it form the list
        logging.debug('ad.receive_response conn %d : %s' % (conn.id, buf))
        self.resps += 1 
        try:
            conn.close()
        except :
            pass
        return ''

    def on_error(self, conn):
        logging.error('ad.on_error : error recived %d' % conn.id)
        self.errors += 1  
        try:
            conn.close()
        except :
            pass

    def no_response(self, conn):
        logging.error('ad.on_error : error no response recived %d' % conn.id)
        self.no_resps += 1        
        try:
            conn.close()
        except :
            pass
