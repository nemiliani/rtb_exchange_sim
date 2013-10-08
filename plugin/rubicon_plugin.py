from parameter_plugin import ParameterPlugin
import random
import logging
import json
import os
import datetime

WIN_PROBABILITY = 9

BASE_PATH = 'plugin/rubicon'

REQUEST_FILES = [ 
    'rubicon_banner1_nw.json',
#    'rubicon_banner2_nw.json',
#    'rubicon_banner3_nw.json',
#    'rubicon_banner4_nw.json',
#    'rubicon_desktop_nw.json',
#    'rubicon_mobile_app_nw.json',
#    'rubicon_mobile_web_nw.json',
#    'rubicon_test1_nw.json'
]

WIN_REQ = '{"account":["padre","hijo","nieto"],"adSpotId":"1","auctionId":"%s","bidTimestamp":0.0,"channels":[],"timestamp":%s,"type":1,"uids":{"prov":"597599535","xchg":"1177748678"},"winPrice":[96,"USD/1M"]}'

class RubiconPlugin(ParameterPlugin):
    '''
        Describes the parameter plugin interface
    '''
    def __init__(self):
        self.request_templates = []
        self.aid = None 

    def initialize(self):
        for name in REQUEST_FILES:
            with open(os.path.join(BASE_PATH, name), 'rb') as f:
                tmp = f.readline()
                self.request_templates.append(tmp)
                logging.debug('plugin.rubicon : loading template %s' % tmp)

    def get_request(self):
        # create the request line
        req_line = 'POST /auctions HTTP/1.1'
        # set the headers
        headers = {}
        headers['Host'] = 'localhost'         
        headers['Connection'] = 'keep-alive'
        headers['Content-Type'] = 'application/json'
        headers['x-openrtb-version'] = '2.1'
        # build a hex auction id
        self.aid = format(
                random.randint(10000000000000, 99999999999999),
                'x')
        # load a random body and set the aid
        body = random.choice(self.request_templates)
        body = body % self.aid
        # set the Content-Length header
        headers['Content-Length'] = str(len(body))
        
        # return the request
        logging.debug('plugin.rubicon : get_request %s' % self.aid)        
        return (req_line, headers, body)

    def receive_response(self, status_code, headers, body):
        logging.debug('plugin.rubicon : receive_response')
        # is it a bid ?
        if status_code == 204 :
            return (False, '', {}, '')
        # throw the dice to see if it's a winner                
        win = random.randint(0, 9) < WIN_PROBABILITY
        if not win:
            return (False, '', {}, '')
        aid = json.loads(body)["seatbid"][0]["bid"][0]["id"][:-2]
        # we won, we need to return True with all
        # all the data used to construct the win
        # notification
        logging.debug('plugin.rubicon : sending win for %s' % aid)
        req_line = 'POST /win?ev=imp&pr=546CF33989B0EF0F&pcid=abc&aid=%s HTTP/1.1' % aid
        headers = {}
        headers['Connection'] = 'keep-alive'
        headers['Content-Type'] = 'application/json'
        delta = (datetime.datetime.now() - \
                    datetime.datetime(1970,1,1)).total_seconds()
        body = WIN_REQ % (aid, str(delta))
        headers['Content-Length'] = str(len(body))
        return (True, req_line, headers, body)

    def receive_win_response(self, status_code, headers, body):
        logging.debug('plugin.rubicon : received_win_response')

    def do(self, watcher, revents):
        logging.debug('plugin.rubicon : doing')
