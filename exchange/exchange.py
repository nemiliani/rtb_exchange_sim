import pyev
import os
import sys
import logging
import socket
import signal
import errno
import weakref
import threading
import Queue

from utils import Worker, Connection

STOPSIGNALS = (signal.SIGINT, signal.SIGTERM)
NONBLOCKING = (errno.EAGAIN, errno.EWOULDBLOCK)
MAX_CONNS = 20

class Exchange(object):

    def __init__(self, dsp_endpoints, balance_conn_timeout):
        '''
            Constructor
            dsp_endpoints : is a list of tuples(endpoint, qps) where
                enpoint is a string like '192.168.10.152:5869'
                and qps is the value indicating queries per
                second for that enpoint.
            balance_conn_timeout : is the time period for rebalancing
                available connections.
        '''
        # list containing tuples in the form 
        # (endpoint, expected qps, current qps)
        self.dest_eps = [ (ep[0], ep[1], 0) for ep in dsp_endpoints]
        self.conns = {}
        self.balance_conn_to = balance_conn_timeout
        self.loop = pyev.default_loop()
        self.watchers = [pyev.Signal(sig, self.loop, self.signal_cb)
                         for sig in STOPSIGNALS]

        self.watchers.append(pyev.Timer(
                                self.balance_conn_to, 
                                self.balance_conn_to, 
                                self.loop,
                                self.balance))

        self.watchers.append(pyev.Timer(
                                self.balance_conn_to, 
                                self.balance_conn_to, 
                                self.loop,
                                self.check_established_connections))
        self.workers = {}
        self.queue = Queue.Queue()
        self.current_connections = 0

    def signal_cb(self, watcher, revents):
        self.stop()

    def stop(self):
        self.loop.stop(pyev.EVBREAK_ALL)
        while self.watchers:
            self.watchers.pop().stop()
        logging.debug("{0}: stopped".format(self))

    def start(self):
        '''
            Start watchers and loop
        '''
        for watcher in self.watchers:
            watcher.start()
        logging.debug("{0}: started".format(self))
        self.loop.start()
        
    def balance(self, watcher, revents):
        '''
            Check your connections and balance
        '''
        logging.debug('balancing ...')
        for item in self.dest_eps :
            # check if the endpoint is registered or
            # if the current qps is lower than expected
            qps = item[1] 
            current_qps = item[2]
            if (item[0] not in self.conns) or (qps > current_qps) :
                # we don't seem to have any connections or we have
                # not reached our expected qps yet, we should open
                # another connection
                if self.current_connections < MAX_CONNS :
                    self.async_connect(item[0])
            else :
                pass                
                
    def async_connect(self, endpoint):
        '''
            Asynchronously connect to an endpoint
        '''
        # create the first connection
        logging.debug('launching async_connect to %s' % endpoint)
        ep = endpoint.split(':')
        ep = (ep[0], int(ep[1]))        
        conn = Connection(ep, self.loop)
        # create the entry
        self.conns[endpoint] = []
        w = Worker(conn, self.queue)
        t = threading.Thread(target=w.do)
        # map the process and worker
        logging.debug('worker %d created' % w.id)
        self.workers[w.id] = w
        # run it
        t.start()


    def check_established_connections(self, watcher, revents):
        logging.debug('checking connections')
        # check any of the workers are done
        go = True        
        while go :
            try :
                worker_id, conn = self.queue.get_nowait()                
                logging.debug('deleting worker %d' % worker_id)
                logging.debug('connection state %s' % conn.state)
                del self.workers[worker_id]
                ep_key = ':'.join([str(i) for i in conn.address])
                if conn.state == Connection.STATE_CONNECTED:
                    # save the connection                    
                    self.conns[ep_key].append(conn)
                    self.current_connections += 1
                else :
                    logging.error('Unable to connect to %s ' % ep_key)
            except Queue.Empty:
                go = False

