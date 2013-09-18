class ParameterPlugin(object):
    '''
        Describes the parameter plugin interface
    '''
    def __init__(self):
        pass
    
    def initialize(self):
        raise NotImplementedError('initialize must be implemeted')

    def do_parameters(self, parameters):
        raise NotImplementedError('do_parameters must be implemeted')
