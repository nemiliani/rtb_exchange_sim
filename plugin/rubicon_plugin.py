from parameter_plugin import ParameterPlugin
import random
import logging

class RubiconPlugin(ParameterPlugin):
    '''
        Describes the parameter plugin interface
    '''
    def __init__(self):
        pass

    def initialize(self):
        pass

    def get_request(self):
        req_line = 'GET / HTTP/1.1'
        headers = {}
        headers['Host'] = 'localhost'         
        headers['Connection'] = 'keep-alive'
        headers['Accept'] = '*/*'
        headers['Content-Type'] = 'application/json'
        aid = random.randint(10000000000000, 99999999999999)        
        body = '{"aid":%d}' % aid
        headers['Content-Length'] = str(len(body))
        return (aid, req_line, headers, body)

    def receive_response(self, status_code, headers, body):
        logging.debug('plugin.receive_response')
        print body
