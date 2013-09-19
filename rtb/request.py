
class RTBRequest(object):
    '''
        Represents a request
    '''
    def __init__(self,
                 aid, 
                 template, 
                 req_line, 
                 headers, 
                 body):
        self.auction_id = aid        
        self.template = template
        self.req_line = req_line
        self.headers = headers
        self.body = body

    def build(self):
        params = {}
        params['REQUEST_LINE'] = '%s\r\n' % self.req_line
        hds = ''
        for k,v in self.headers.iteritems():
            hds += '%s: %s\r\n' % (k,v)
        params['HEADERS'] = '%s\r\n' % hds
        params['BODY'] = self.body
        s = self.template.render(**params)[:-1]
        return s

if __name__ == '__main__' :

    from mako.template import Template
    mytemplate = Template(
        filename='/home/or3st3s/workspace/usmc/pseudo_exchange/templates/request.template')
    req_line = 'POST /auctions/ HTTP/1.1'
    headers = {
        'Connection': 'keep-alive',
        'Content-Type': 'application/json'
    }
    body = '{"aid":5}'   
    req = RTBRequest(5, mytemplate, req_line, headers, body)
    print req.build()
