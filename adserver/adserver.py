import pyev
import os
import sys
import logging
import socket
import signal
import errno

from settings import  EVENT_ENDPOINT
from utils import EphemeralConnection

class AdServer(object):

    def __init__(self, loop):
        self.loop = loop
        self.watchers = []
        ep = EVENT_ENDPOINT.split(':')
        self.endpoint = (ep[0], int(ep[1]))
        self.conns = {}
        self.timers = {}
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
        for k,v in self.timers.iteritems():
            v.stop()
        for k,v in self.conns.iteritems():
            try :
                v.close()
            except :
                pass
        logging.debug("{0}: stopped".format(self))

    def print_stats(self, watcher, revents):
        logging.info(
            'evs=%d reps=%d errs=%d noresps=%d, endpoint=%s:%d, conns=%d' % 
            (self.reqs, self.resps, self.errors, self.no_resps, 
            self.endpoint[0], self.endpoint[1], len(self.conns)))

    def send_event(self, buf, timeout):
        # set the timeout to call the method that will
        # create the connection and send the buffer (send buffer)
        conn = EphemeralConnection(
                self.loop, self.endpoint, buf, self.recv_http, 
                self.on_error, self.no_response)
        self.conns[conn.id] = conn
        self.timers[conn.id] = pyev.Timer(
                timeout, 0.0, self.loop, self.send_http, conn_id)
        self.timers[conn.id].start()

    def send_http(self, conn_id):
        # create the ad connection, set the buff
        # and recv_http callback and the connect to send it
        try:
            self.conns[conn_id].connect()
            self.reqs += 1
        except KeyError :
            logging.error('AdServer : no conn %d found' % conn_id)
        except :
            logging.error('AdServer : error sending http')
            self.conns[conn_id].close()
            del self.conns[conn_id]
        self.timers[conn_id].stop()
        del self.timers[conn_id]
            
       
    def recv_http(self, buf, conn):
        # receive the response, maybe pint the status code,
        # close the connection and erase it form the list
        logging.debug('ad.receive_response conn %d : %s' % (conn.id, buf))
        self.resps += 1        
        try:
            self.conns[conn_id].close()
            del self.conns[conn_id]
        except :
            pass
        return ''

    def on_error(self, conn):
        logging.error('ad.on_error : error recived %d' % conn.id)
        self.errors += 1        
        try:
            self.conns[conn_id].close()
            del self.conns[conn_id]
        except :
            pass

    def no_response(self, conn):
        logging.error('ad.on_error : error no response recived %d' % conn.id)
        self.no_resps += 1        
        try:
            self.conns[conn_id].close()
            del self.conns[conn_id]
        except :
            pass
