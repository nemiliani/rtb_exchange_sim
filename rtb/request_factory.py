from mako.template import Template
import random
import logging

from request import RTBRequest
from response import RTBResponse

class RTBRequestFactory(object):
    '''
        Handles creation and mapping of requests
    ''' 
    def __init__(self, template_file):
        self.template_file = template_file
        self.template = None
        self.plugin_instance = None
     
    def initialize(self):
        # read the template file        
        self.template = Template(filename=self.template_file)
    
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
            req_line, headers, body = \
                self.plugin_instance.get_request()
        req = RTBRequest(self.template, 
                        req_line, 
                        headers, 
                        body)
        return req.build()

    def receive_response(self, buf):
        '''
            Receives a response buffer and checks if 
            it has a full HTTP response, if it does
            it invokes the plugin and returns an empty
            buffer, otherwise the buffer is returned as
            it was passed
        '''
        logging.debug('receive_response')
        response = RTBResponse()
        ok, parser = response.receive_buffer(buf)
        if ok :
            if self.plugin_instance :
               win, req_line, headers, body = \
                     self.plugin_instance.receive_response(
                        parser.get_status_code(), 
                        parser.get_headers(), 
                        parser.recv_body())
            return ('', win, req_line, headers, body)
        else:
            return (buf, None, None, None, None)
        
    def create_win_request(self, req_line, headers, body):
        '''
            Creates a win request and returns the buffer
            to be sent by the connection
        '''
        logging.debug('create_win_request')
        req = RTBRequest(self.template, 
                        req_line, 
                        headers, 
                        body)
        return req.build()

    def receive_win_response(self, buf):
        '''
            Receives a win response buffer and checks if 
            it has a full HTTP response, if it does
            it invokes the plugin and returns an empty
            buffer, otherwise the buffer is returned as
            it was passed
        '''
        logging.debug('receive_win_response')
        response = RTBResponse()
        ok, parser = response.receive_buffer(buf)
        if ok and self.plugin_instance :
            self.plugin_instance.receive_win_response(
                        parser.get_status_code(), 
                        parser.get_headers(), 
                        parser.recv_body())
            return ''
        return buf
