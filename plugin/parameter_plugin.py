class ParameterPlugin(object):
    '''
        Describes the parameter plugin interface
    '''
    def __init__(self):
        pass
    
    def initialize(self):
        raise NotImplementedError('initialize must be implemeted')

    def get_request(self):
        raise NotImplementedError('do_parameters must be implemeted')

    def receive_response(self, status_code, headers, body):
        raise NotImplementedError('receive_response must be implemeted')

    def receive_win_response(self, status_code, headers, body):
        raise NotImplementedError('receive_win_response must be implemeted')

    def do(self, watcher, revents):
        raise NotImplementedError('do must be implemeted')
