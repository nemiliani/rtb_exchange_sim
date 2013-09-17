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

from utils import Worker, WorkerPool, Connection, NONBLOCKING

STOPSIGNALS = (signal.SIGINT, signal.SIGTERM)
MAX_CONNS = 1

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
        self.awaiting_conns = {}
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
            #load up
            endpoint = item[0]            
            qps = item[1]
            # update current_qps
            if endpoint in self.conns :
                current = 0
                for conn in self.conns[endpoint]:
                    current += conn.last_qps 
                item[2] = current
            current_qps = item[2]
            logging.info('qps=%d endpoint=%s' % (current_qps, endpoint))
            # check if the endpoint is registered or
            # if the current qps is lower than expected
            if (endpoint not in self.conns) or (qps > current_qps) :
                # we don't seem to have any connections or we have
                # not reached our expected qps yet, we should open
                # another connection
                if self.current_connections < MAX_CONNS :
                    self.async_connect(endpoint)
                else :
                    logging.warning('MAX_CONNS %d reached' % MAX_CONNS)

    def async_connect(self, endpoint):
        '''
            Asynchronously connect to an endpoint
        '''
        # create the connection
        logging.debug('launching async_connect to %s' % endpoint)
        ep = endpoint.split(':')
        ep = (ep[0], int(ep[1]))        
        conn = Connection(self, ep, self.loop)
        self.awaiting_conns[conn.id] = conn
        self.current_connections += 1
        # create the entry
        if endpoint not in self.conns :
            self.conns[endpoint] = []
        state = conn.connect()
        if state == Connection.STATE_CONNECTING:
           logging.debug('connecting!')

    def check_established_connections(self, watcher, revents):
        logging.debug('checking connections')
        # check if any of the awaiting_conns are done
        for cid, conn in self.awaiting_conns.items():
            ep_key = ':'.join([str(i) for i in conn.address])
            if conn.state == Connection.STATE_CONNECTED:
                logging.info('connected to %s ' % ep_key)                
                # save the connection                    
                self.conns[ep_key].append(conn)
                # remove from awaiting_conns
                del self.awaiting_conns[cid]
            elif conn.state == Connection.STATE_CONNECTING:
                logging.info('still trying to connect to %s ' % ep_key)
            else :
                logging.error('unable to connect to %s ' % ep_key)
                # remove from awaiting_conns
                self.awaiting_conns[cid].close()
                del self.awaiting_conns[cid]
                self.current_connections -= 1
                logging.error('unable to connect to end')


    def remove_connection(self, conn):
        logging.error('removing connection %d' % conn.id)
        self.current_connections -= 1
        ep_key = ':'.join([str(i) for i in conn.address])
        self.conns[ep_key].remove(conn)

