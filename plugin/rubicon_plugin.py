from parameter_plugin import ParameterPlugin
import random
class RubiconPlugin(ParameterPlugin):
    '''
        Describes the parameter plugin interface
    '''
    def __init__(self):
        pass

    def initialize(self):
        pass

    def get_request(self):
        req_line = 'POST /auctions/ HTTP/1.1'
        headers = {}        
        headers['Connection'] = 'keep-alive'
        headers['Content-Type'] = 'application/json'
        aid = random.randint(10000000000000, 99999999999999)        
        body = '{"aid":%d}' % aid
        headers['Content-Length'] = str(len(body))
        return (aid, req_line, headers, body)
