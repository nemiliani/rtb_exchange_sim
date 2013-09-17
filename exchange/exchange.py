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

from utils import Worker, WorkerPool, Connection

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
        self.dest_eps = [ [ep[0], ep[1], 0] for ep in dsp_endpoints]
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
        self.worker_pool = WorkerPool(self.queue, 5)

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
            endpoint = item[0]            
            qps = item[1] 
            current_qps = item[2]
            if (endpoint not in self.conns) or (qps > current_qps) :
                # we don't seem to have any connections or we have
                # not reached our expected qps yet, we should open
                # another connection
                if self.current_connections < MAX_CONNS :
                    self.async_connect(endpoint)
                else :
                    logging.warning('MAX_CONNS %d reachead' % MAX_CONNS)
            if endpoint in self.conns :
                # update current_qps
                current = 0
                for conn in self.conns[endpoint]:
                    current = conn.current_qps 
                item[2] = current

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
        w = self.worker_pool.get_worker()
        if not w :
            logging.warning('Worker pool exausted')
            return     
        w.conn = conn
        self.workers[w.id] = w
        w.run()


    def check_established_connections(self, watcher, revents):
        logging.debug('checking connections')
        # check any of the workers are done
        go = True        
        while go :
            try :
                worker_id, conn = self.queue.get_nowait()                
                logging.debug('deleting worker %d' % worker_id)
                logging.debug('connection state %s' % conn.state)
                self.worker_pool.set_worker(self.workers[worker_id])
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

