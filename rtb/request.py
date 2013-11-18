import logging

class RTBRequest(object):
    '''
        Represents a request
    '''
    def __init__(self, 
                 template, 
                 req_line, 
                 headers, 
                 body):        
        self.template = template
        self.req_line = req_line
        self.headers = headers
        self.body = body

    def is_ascii(self, s):
        return all(ord(c) < 128 for c in s)

    def build(self):
        hds = '%s\r\n' % self.req_line
        for k,v in self.headers.iteritems():
            hds += '%s: %s\r\n' % (k,v)
        hds += '\r\n%s' % self.body
        if not self.is_ascii(hds):
            hds = unicode(hds, 'utf-8')
        logging.debug('rendering done %s' % type(hds))
        return hds

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
