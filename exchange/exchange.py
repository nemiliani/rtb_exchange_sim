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
from settings import MAX_CONNS, MAX_EVENT_CONNS, CHECK_CONNS_TO, CHECK_PENDING_TO, \
                    TEMPLATE_FILENAME, EVENT_ENDPOINT, PARAMETER_PLUGIN, \
                    KEEP_ALIVE_HTTP_REQUEST, EVENT_CONN_KEEP_ALIVE_TO
from rtb import RTBRequestFactory

STOPSIGNALS = (signal.SIGINT, signal.SIGTERM)

class Exchange(object):

    def __init__(self, dsp_endpoints, event_endpoint, balance_conn_timeout):
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
        self.event_endpoint = event_endpoint
        self.conns = {}
        self.awaiting_conns = {}
        self.event_conn_queue = []
        self.event_conns = {}
        self.event_connections = 0
        self.keep_alive_resp_waiting = {}        
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
                                CHECK_CONNS_TO, 
                                CHECK_CONNS_TO, 
                                self.loop,
                                self.check_established_connections))

        self.watchers.append(pyev.Timer(
                                CHECK_PENDING_TO, 
                                CHECK_PENDING_TO, 
                                self.loop,
                                self.check_pending_wins))

        self.watchers.append(pyev.Timer(
                                EVENT_CONN_KEEP_ALIVE_TO, 
                                EVENT_CONN_KEEP_ALIVE_TO, 
                                self.loop,
                                self.send_keep_alives))

        self.current_connections = 0
        self.request_fact = RTBRequestFactory(
                                    TEMPLATE_FILENAME)
        self.request_fact.initialize()
        self.request_fact.set_parameter_plug(PARAMETER_PLUGIN)
        self.pending_wins = []

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
        # start generic watchers for times and signals        
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
            logging.info('qps=%d endpoint=%s conns=%d' % 
                            (current_qps, endpoint, self.current_connections))
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
        conn = Connection(
                ep, 
                self.loop, 
                self.create_request, 
                self.receive_response, 
                self.remove_connection,
                None)
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
                logging.debug('bid connecting with id %d' % conn.id)        
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
        try :
            self.conns[ep_key].remove(conn)
        except ValueError:
            logging.info('connection %d was not yet persisted' % conn.id)

    def receive_response(self, read_buf, conn):
        logging.debug('ex.receive_response')
        buf, win, req_line, headers, body = \
            self.request_fact.receive_response(read_buf)
        if (not buf) and win :
            # the buf was a full response and the 
            # auction was won, call the request factory
            # to create a win request notification
            buf = self.request_fact.create_win_request(
                                            req_line, headers, body)
            # send it
            self.send_win_notification(buf)
            return ''
        elif buf and win is None:
            # this means that the buf was not a complete response
            return buf
        else:
            # this means that the buf was  a complete response
            # but we did not win
            return ''

    def create_request(self, conn):
        logging.debug('ex.create_request')
        return self.request_fact.create_request()    

    def send_win_notification(self, buf):
        logging.debug('ex.send_win_response')
        # do we have any connections available
        conn = self.get_event_connection()
        if not conn:
            logging.debug('ex.buffering win')
            self.pending_wins.append(buf)
            return
        # request an event to send the buffer
        conn.send_buffer(buf)

    def get_event_connection(self):
        logging.debug('ex.get_event_connection')
        # any connections left ?
        if len(self.event_conn_queue):
            return self.event_conn_queue.pop(0)
        # No available connections, can we create 
        # another one?
        if not self.event_connections < MAX_EVENT_CONNS:
            return None
        # create another one
        ep = EVENT_ENDPOINT.split(':')
        ep = (ep[0], int(ep[1]))
        self.event_connections += 1
        conn = Connection(
                ep, 
                self.loop, 
                self.create_win_request, 
                self.receive_win_response, 
                self.remove_event_connection,
                None)
        state = conn.connect()
        if state == Connection.STATE_CONNECTING:
           logging.debug('event connecting with id %d' % conn.id)
        self.event_conns[conn.id] = conn       
        return conn
    
    def create_win_request(self, conn):
        # we can pass since we set the buffer at
        # send_win_notification
        logging.error('This method should not ever be invoked')
        return ''

    def receive_win_response(self, read_buf, conn):
        logging.debug('ex.receive_win_response')
        self.event_conn_queue.append(conn)
        # set the connection into IDLE mode so that after
        # receiving the in response we don't register a
        # WRITE event
        conn.state = Connection.STATE_IDLE
        if conn.id in self.keep_alive_resp_waiting:
            del self.keep_alive_resp_waiting[conn.id]
            return ''
        return self.request_fact.receive_win_response(read_buf) 

    def remove_event_connection(self, conn):
        logging.debug('ex.remove_event_connection %d', conn.id)
        try :
            self.event_connections -= 1
            self.event_conn_queue.remove(conn)
            del self.event_conns[conn.id]
        except :
            logging.info(
                'unable to remove event conn %d, it was not queued',
                 conn.id)

    def check_pending_wins(self,  watcher, revents):
        logging.debug('ex.check_pending_wins %d' % len(self.pending_wins))
        # get the amount of idle connections        
        wins = len(self.pending_wins)
        for i in range(wins):
            try :
                conn = self.get_event_connection()
                if conn :
                    logging.debug('ex. sending pending win')
                    conn.send_buffer(self.pending_wins.pop(0))
                else :
                    break
            except IndexError:
                break

    def send_keep_alives(self,  watcher, revents):
        logging.debug('ex.send_keep_alives')
        buf = KEEP_ALIVE_HTTP_REQUEST % EVENT_CONN_KEEP_ALIVE_TO
        for i in range(len(self.event_conn_queue)):
            conn = self.event_conn_queue.pop(0)
            conn.send_buffer(buf)
            self.keep_alive_resp_waiting[conn.id] = conn
        
