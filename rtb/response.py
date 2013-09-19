from http_parser.parser import HttpParser

class RTBResponse(object):

    def __init__(self):
        self.buffer = ''

    def receive_buffer(self, buf):
        self.buffer += buf
        parser = HttpParser()
        recved = len(self.buffer)
        nparsed = parser.execute(self.buffer, recved)
        assert nparsed == recved
        if parser.is_message_complete():
            return (True, parser)
        return (False, parser)

if __name__ == '__main__' :

    print 'http res'
    rsp = ''
    with open('../testing/response.http', 'r') as f:
        rsp = f.readlines()
        rsp = ''.join(rsp)
        rsp = rsp[:-2]
        print 'buffer :'
        print rsp
    print 'parsing ...'
    p = HttpParser()
    recved = len(rsp)
    nparsed = p.execute(rsp, recved)
    assert nparsed == recved

    if p.is_message_complete():
        print 'message complete'
    
    print '--------------------'

    rsp_1 = ''
    with open('../testing/test1_response_part1.http', 'r') as f:
        rsp_1 = f.readlines()
        rsp_1 = ''.join(rsp_1)
        rsp_1 = rsp_1[:-2]
    rsp_2 = ''
    with open('../testing/test1_response_part2.http', 'r') as f:
        rsp_2 = f.readlines()
        rsp_2 = ''.join(rsp_2)
        rsp_2 = rsp_2[:-2]

    p = HttpParser()
    recved = len(rsp_1)
    nparsed = p.execute(rsp_1, recved)
    assert nparsed == recved

    if p.is_message_complete():
        print 'message complete'
    else :
        print 'message incomplete'
        print p.recv_body()

    recved = len(rsp_2)
    nparsed = p.execute(rsp_2, recved)
    assert nparsed == recved

    if p.is_message_complete():
        print 'message complete'
        print p.recv_body()
        print p.get_headers()
    else :
        print 'message incomplete'
        print p.recv_body()

    print '--------------------'

    rsp_1 = ''
    with open('../testing/test2_response_part1.http', 'r') as f:
        rsp_1 = f.readlines()
        rsp_1 = ''.join(rsp_1)
        rsp_1 = rsp_1[:-2]
    rsp_2 = ''
    with open('../testing/test2_response_part2.http', 'r') as f:
        rsp_2 = f.readlines()
        rsp_2 = ''.join(rsp_2)
        rsp_2 = rsp_2[:-2]

    p = HttpParser()
    recved = len(rsp_1)
    nparsed = p.execute(rsp_1, recved)
    assert nparsed == recved

    if p.is_message_complete():
        print 'message complete'
    else :
        print 'message incomplete'
        print p.recv_body()

    recved = len(rsp_2)
    nparsed = p.execute(rsp_2, recved)
    assert nparsed == recved

    if p.is_message_complete():
        print 'message complete'
        print p.recv_body()
        print p.get_headers()
    else :
        print 'message incomplete'
        print p.recv_body()

    print '--------------------'

    rsp_1 = ''
    with open('../testing/test2_response_part1.http', 'r') as f:
        rsp_1 = f.readlines()
        rsp_1 = ''.join(rsp_1)
        rsp_1 = rsp_1[:-2]
    rsp_2 = ''
    with open('../testing/test2_response_part2.http', 'r') as f:
        rsp_2 = f.readlines()
        rsp_2 = ''.join(rsp_2)
        rsp_2 = rsp_2[:-2]

    p = RTBResponse()
    ok, parser = p.receive_buffer(rsp_1)
    if parser.is_message_complete():
        print 'message complete'
        print parser.recv_body()
    else :
        print 'message incomplete'

    rsp_1 += rsp_2
    ok, parser =  p.receive_buffer(rsp_1)
    if parser.is_message_complete():
        print 'message complete'
        print parser.recv_body()
    else :
        print 'message incomplete'
