from parameter_plugin import ParameterPlugin
from string import Template
import random
import json
import logging
from urlparse import urlparse

# CONFIG (see to put this in any other part; aka not global)
from render_utils import incrementor
RENDER_MAP = {
              'auction_id' : incrementor(12345678)}
BODY_TEMPLATES = ['plugin/mopub/mopub_body1.tmpl', 
                  'plugin/mopub/mopub_body2.tmpl']
HEH_ENDPOINT_TMPL = "http://localhost:8080/impression/${exchange}/${AUCTION_ID}/${AUCTION_PRICE}?impid=${AUCTION_IMP_ID}"
AD_SERVER_ENDPOINT_TMPL = "http://localhost:8080/events?ev=imp&aid=${AUCTION_ID}&apr=${AUCTION_PRICE}&sptid=${AUCTION_IMP_ID}"
USE_HEH_ENDPOINT = False
HTTP_RESOURCE = 'mopub'


class OpenRTBPlugin(ParameterPlugin):
    '''
        Generic Open Rtb plugin
    '''
    def __init__(self):
        self.request_body_templates = []
        self.render_map = {}
        self.tmpl_notif = ''
    
    def initialize(self, adserver):
        
        self.adserver = adserver
        
        self.render_map = RENDER_MAP
        self.request_body_templates_files = BODY_TEMPLATES
        
        # Create templates...
        for filename in self.request_body_templates_files:
            with open(filename) as f:
                logging.info('Using file template %s' % filename)
                tmpl = Template(''.join(f.readlines()))
                self.request_body_templates.append(tmpl)
        
        # Template for notification endpoint
        if USE_HEH_ENDPOINT :
            self.tmpl_notif_file = HEH_ENDPOINT_TMPL
        else :
            self.tmpl_notif_file = AD_SERVER_ENDPOINT_TMPL
        self.tmpl_notif = Template(self.tmpl_notif_file)

    def get_request(self):
        # We need to return a request line, a map of headers and a body string
        
        # Create the request line
        req_line = 'POST /%s HTTP/1.1' % HTTP_RESOURCE
        
        # Set the headers
        headers = {}
        headers['Host'] = 'localhost'
        headers['Connection'] = 'keep-alive'
        headers['Content-Type'] = 'application/json'
        headers['x-openrtb-version'] = '2.1'
        
        # Render the body...
        tmpl = random.choice(self.request_body_templates)
        fun_rendered_map = { k : fun() for k, fun in self.render_map.items()}
        body = tmpl.substitute(fun_rendered_map)
        
        # Set the header size
        headers['Content-Length'] = len(body)
        
        logging.debug('Message body being sent :')
        logging.debug(body)
        return (req_line, headers, body)

    def receive_response(self, status_code, headers, body):
        # If it is not a bid, do nothing
        if status_code == 204 :
            return (False, '', {}, '')
        
        # Extract data from bid response
        js = json.loads(body)
        logging.debug("Response received :")
        logging.debug(str(js))
        price = js['seatbid'][0]['bid'][0]['price']
        auction_id = js['id']
        spot_id = js['seatbid'][0]['bid'][0]['impid']
        
        # With that data, create the notification...
        notif_render = { 'AUCTION_PRICE' : price,
                         'AUCTION_ID' : auction_id,
                         'AUCTION_IMP_ID' : spot_id,
                         'exchange' : 'mopub'}
        url = self.tmpl_notif.substitute(notif_render)
        self.__send_impression_notification(url)
        return (False, '', {}, '')
        
        
    def __send_impression_notification(self, url):
        parsed_url = urlparse(url)
        req_line = 'GET %s?%s HTTP/1.1' % (parsed_url.path,
                                           parsed_url.query)
        headers = {}
        headers['Host'] = 'localhost'
        heads = self.__headers_to_str(headers)
        buf = '%s\r\n%s\r\n' % (req_line, heads)
        
        # send the impression event in 0.1 secs
        logging.debug("Sending notification :")
        logging.debug(buf)
        self.adserver.send_event(buf, 0.1)
        
    def __headers_to_str(self, headers):
        heads = ''
        for k,v in headers.iteritems():
            heads += '%s: %s\r\n' % (k, v)
        return heads


    def receive_win_response(self, status_code, headers, body):
        logging.debug('received_win_response')

    def do(self, watcher, revents):
        logging.info('doing...')
