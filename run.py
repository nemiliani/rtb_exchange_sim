#!/usr/bin/python
import gc
from exchange import Exchange
import logging

from settings import ENDPOINT_LIST, EVENT_ENDPOINT, BALANCE_TO, LOG_LEVEL

if __name__ == '__main__':
    gc.disable()
    logging.basicConfig(
            level=LOG_LEVEL, 
            format='%(asctime)-15s %(levelname)s %(message)s')
    x = Exchange(ENDPOINT_LIST , EVENT_ENDPOINT, BALANCE_TO)
    x.start()
