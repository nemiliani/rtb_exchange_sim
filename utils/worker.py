import logging

class Worker:

    _id = 1

    def __init__(self, conn, queue):
        self.queue = queue
        self.conn = conn
        self.id = Worker._id
        Worker._id += 1
 
    def do(self):
        logging.debug('worker.doing')
        self.conn.connect()
        self.queue.put((self.id, self.conn))
        logging.debug('worker.done')

    
