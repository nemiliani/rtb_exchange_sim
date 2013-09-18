import logging

# Max connections allowed for the process
MAX_CONNS = 100

# Endpoint list cointaingn tuples (endpoint, expected_qps) where :
#  - endpoint souhld be a string 'host:port'
#  - expected_qps is the amount of qps expected for the endpoint
ENDPOINT_LIST = [
    ('localhost:9876', 3000),
]

# Balance time out indicating the period in seconds 
# to balance connections
BALANCE_TO = 3

# Check connections time out indicating the period in
# seconds to verify if a connection attempt was successfull
CHECK_CONNS_TO = 1

# Log level should be one of :
# - logging.DEBUG
# - logging.INFO
# - logging.WARNING
# - logging.ERROR
LOG_LEVEL = logging.INFO


