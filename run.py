from exchange import Exchange
import logging


if __name__ == '__main__':

    logging.basicConfig(
            level=logging.DEBUG, 
            format='%(asctime)-15s %(levelname)s %(message)s')
    x = Exchange([('localhost:9876',5), ], 3)
    x.start()
