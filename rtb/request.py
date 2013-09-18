
class RTBRequest(object):
    '''
        Represents a request
    '''
    def __init__(self, auction_id, parameters, template):
        self.auction_id = auction_id
        self.params = parameters
        self.template = template

    def build(self):
        return self.template.render(**self.params)
