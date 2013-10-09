from parameter_plugin import ParameterPlugin
import random
import logging
import json
import datetime

BID_REQ = '{"id":%d, "timestamp":%s,"isTest":false,"url":"http://datacratic.com/","language":"en","exchange":"mock","location":{"countryCode":"CA","regionCode":"QC","cityName":"Montreal","dma":-1,"timezoneOffsetMinutes":-1},"userIds":{"prov":"4083789604","xchg":"3715852675"},"imp":[{"id":1,"formats":["160x600"],"position":0},{"id":2,"formats":["160x600"],"position":0}],"spots":[{"id":1,"formats":["160x600"],"position":0},{"id":2,"formats":["160x600"],"position":0}]}'

WIN_REQ = '{"account":["hello","world"],"adSpotId":"1","auctionId":"%d","bidTimestamp":0.0,"channels":[],"timestamp":%s,"type":1,"uids":{"prov":"597599535","xchg":"1177748678"},"winPrice":[96,"USD/1M"]}'

class DatacraticPlugin(ParameterPlugin):
    '''
        Describes the parameter plugin interface
    '''
    def __init__(self):
        self.aid = None

    def initialize(self, adserver):
        self.adserver = adserver

    def get_request(self):
        req_line = 'POST /bids HTTP/1.1'
        headers = {}
        headers['Host'] = 'localhost'         
        headers['Connection'] = 'keep-alive'
        headers['Content-Type'] = 'application/json'
        self.aid = random.randint(1000000000, 9999999999)
        delta = (datetime.datetime.now() - \
                    datetime.datetime(1970,1,1)).total_seconds()
        body = BID_REQ % (self.aid, str(delta))
        logging.debug('plugin.get_request %d' % self.aid)
        headers['Content-Length'] = str(len(body))
        return (req_line, headers, body)

    def receive_response(self, status_code, headers, body):
        logging.debug('plugin.receive_response')
        # throw the dice to see if it's a winner                
        win = random.randint(0, 9) < 3
        req_line = ''
        headers = {}
        body = ''
        if not win :
            return (False, req_line, headers, body)
        # we won, we need to return True with all
        # all the data used to construct the win
        # notification
        req_line = 'POST /win HTTP/1.1'
        headers = {}
        headers['Connection'] = 'keep-alive'
        headers['Content-Type'] = 'application/json'
        delta = (datetime.datetime.now() - \
                    datetime.datetime(1970,1,1)).total_seconds()
        body = WIN_REQ % (self.aid, str(delta))
        headers['Content-Length'] = str(len(body))
        return (True, req_line, headers, body)

    def receive_win_response(self, status_code, headers, body):
        logging.debug('plugin.receive_win_response')

    def do(self, watcher, revents):
        logging.debug('plugin.do')


