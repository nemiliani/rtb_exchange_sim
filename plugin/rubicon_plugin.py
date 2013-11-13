from parameter_plugin import ParameterPlugin
import random
import logging
import json
import os
import datetime

WIN_PROBABILITY   = 3
CLICK_PROBABILITY = 1

BASE_PATH = 'plugin/rubicon_test'

REQUEST_FILES = [
    'rubicon_banner01_nw.json',
    'rubicon_banner02_nw.json',
    'rubicon_banner03_nw.json',
    'rubicon_banner04_nw.json',
    'rubicon_banner05_nw.json',
    'rubicon_banner06_nw.json',
    'rubicon_banner07_nw.json',
    'rubicon_banner08_nw.json',
    'rubicon_banner09_nw.json',
    'rubicon_banner10_nw.json',
    'rubicon_banner11_nw.json',
    'rubicon_banner12_nw.json',
    'rubicon_banner13_nw.json',
    'rubicon_banner14_nw.json',
    'rubicon_banner15_nw.json',
    'rubicon_banner16_nw.json',
    'rubicon_banner17_nw.json',
    'rubicon_banner18_nw.json',
    'rubicon_banner19_nw.json',
    'rubicon_banner20_nw.json',
]


WIN_REQ = '{"account":["padre","hijo","nieto"],"adSpotId":"1","auctionId":"%s","bidTimestamp":0.0,"channels":[],"timestamp":%s,"type":1,"uids":{"prov":"597599535","xchg":"1177748678"},"winPrice":[96,"USD/1M"]}'

class RubiconPlugin(ParameterPlugin):
    '''
        Describes the parameter plugin interface
    '''
    def __init__(self):
        self.request_templates = []
        self.aid = None 

    def initialize(self, adserver):
        self.adserver = adserver
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
        js = json.loads(body)
        aid = js["seatbid"][0]["bid"][0]["id"][:-2]
        pcid = js["seatbid"][0]["bid"][0]["crid"]
        # we won, we need to return True with all
        # all the data used to construct the win
        # notification
        #logging.debug('plugin.rubicon : sending win for %s' % aid)
        #req_line = 'POST /win?ev=imp&auctionPrice=546CF33989B0EF0F' \
        #            '&publisherCreativeId=abc&auctionId=%s HTTP/1.1' % aid
        req_line = 'GET /trackImpression/%s/auctionId/%s/auctionPrice/546CF33989B0EF0F?externalSystemId=hola HTTP/1.1' % (pcid, aid)
        headers = {}
        headers['Host'] = 'localhost'
        headers['Content-Type'] = 'application/json'
        delta = (datetime.datetime.now() - \
                    datetime.datetime(1970,1,1)).total_seconds()
        body = WIN_REQ % (aid, str(delta))
        headers['Content-Length'] = str(len(body))
        heads = self.headers_to_str(headers)
        buf = '%s\r\n%s\r\n%s' % (req_line, heads, body)
        # send the impression event in 0.5 secs
        self.adserver.send_event(buf, 0.5)
        # roll the dice to see if we should click
        click = random.randint(0, 100) < CLICK_PROBABILITY
        if not click:
            return (False, '', {}, '')
        #click_req_line = 'POST /click?ev=click' \
        #            '&publisherCreativeId=abc&auctionId=%s HTTP/1.1' % aid
        click_req_line = 'GET /clicktracking/chupala/connector/%s?auctionId=%s&externalSystemId=hola&url=http://www.sis.com HTTP/1.1' % (pcid, aid)
        buf_click = '%s\r\n%s\r\n%s' % (click_req_line, heads, body)
        self.adserver.send_event(buf_click, 1.8)
        return (False, '', {}, '')

    def receive_win_response(self, status_code, headers, body):
        logging.debug('plugin.rubicon : received_win_response')

    def do(self, watcher, revents):
        logging.debug('plugin.rubicon : doing')

    def headers_to_str(self, headers):
        heads = ''
        for k,v in headers.iteritems():
            heads += '%s: %s\r\n' % (k, v)
        return heads
