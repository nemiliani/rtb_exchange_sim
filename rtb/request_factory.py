from mako.template import Template
import random
import logging

from request import RTBRequest

class RTBRequestFactory(object):
    '''
        Handles creation and mapping of requests
    ''' 
    def __init__(self, 
            bottom_auction_id,
            top_auction_id,
            template_file):
        self.bottom_aid = bottom_auction_id
        self.top_aid = top_auction_id
        self.template_file = template_file
        self.requests = {}
        self.template = None
        self.plugin_instance = None
     
    def initialize(self):
        # read the template file        
        self.template = Template(filename=self.template_file)
    
    def get_next_auction_id(self):
        '''
            Get the next auction id
        '''                
        aid = random.randint(
                self.bottom_aid, self.top_aid)
        while aid in self.requests :
            aid = random.randint(
                self.bottom_aid, self.top_aid)
        return aid
    
    def set_parameter_plug(self, plugin):
        '''
            Set a param class plugin, this must implement
            the ParameterPlugin interface
        '''
        self.plugin_instance = plugin()
        self.plugin_instance.initialize()

    def create_request(self, set_aid=True):
        '''
            Create a request and call the parameter plugin
        '''
        logging.debug('create_request')
        aid = None
        req_line = ''
        headers = {}
        body = ''
        if self.plugin_instance :
            aid, req_line, headers, body = \
                self.plugin_instance.get_request()
        req = RTBRequest(aid, 
                        self.template, 
                        req_line, 
                        headers, 
                        body)
        self.requests[req.auction_id] = req
        return req.build()
        
