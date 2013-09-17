import logging
import threading

class Worker(object):

    _id = 1

    def __init__(self, queue):
        Worker._id += 1        
        self.queue = queue
        self.conn = None
        self.id = Worker._id
        self.thread = threading.Thread(target=self.do)    
        self.ev = threading.Event()        
        self.ev.clear()
        self.thread.start()

    def do(self):
        while True :
            logging.debug('worker %d is waiting' % self.id)
            self.ev.wait()
            logging.debug('worker %d doing' % self.id)
            self.conn.connect()
            self.queue.put((self.id, self.conn))
            logging.debug('worker %d done', self.id)
            self.ev.clear()

    def run(self):
        self.ev.set()

class WorkerPool(object):

    def __init__(self, queue, size):
        self.pool = [ Worker(queue) for i in range(size)]
    
    def get_worker(self):
        if len(self.pool):
            return self.pool.pop()
        return None

    def set_worker(self, worker):
        worker.conn = None
        self.pool.append(worker)
