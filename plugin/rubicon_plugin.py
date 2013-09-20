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
        return (req_line, headers, body)

    def receive_response(self, status_code, headers, body):
        logging.debug('plugin.receive_response')
        # throw the dice to see if it's a winner                
        win = random.randint(0, 9) < 5
        req_line = ''
        headers = {}
        body = ''
        if not win :
            return (False, req_line, headers, body)
        # we won, we need to return True with all
        # all the data used to construct the win
        # notification
        req_line = 'GET / HTTP/1.1'
        headers = {}
        headers['Host'] = 'localhost'         
        headers['Connection'] = 'keep-alive'
        headers['Accept'] = '*/*'
        headers['Content-Type'] = 'application/json'
        aid = random.randint(10000000000000, 99999999999999)        
        body = '{"aid":%d}' % aid
        headers['Content-Length'] = str(len(body))
        return (True, req_line, headers, body)

    def receive_win_response(self, status_code, headers, body):
        pass
