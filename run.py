#!/usr/bin/python

from exchange import Exchange
import logging

from settings import ENDPOINT_LIST, BALANCE_TO, LOG_LEVEL

if __name__ == '__main__':

    logging.basicConfig(
            level=LOG_LEVEL, 
            format='%(asctime)-15s %(levelname)s %(message)s')
    x = Exchange(ENDPOINT_LIST , BALANCE_TO)
    x.start()
