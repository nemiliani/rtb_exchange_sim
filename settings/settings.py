import logging

# Plugin imports
from plugin.rubicon_plugin import RubiconPlugin

# Max connections allowed for the process
MAX_CONNS = 100

# Endpoint list cointaingn tuples (endpoint, expected_qps) where :
#  - endpoint souhld be a string 'host:port'
#  - expected_qps is the amount of qps expected for the endpoint
ENDPOINT_LIST = [
    ('localhost:9876', 1),
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
LOG_LEVEL = logging.DEBUG


# Indicates the minimum auction id
BOTTOM_AUCTION_ID = 10000000000000

# Indicates the maximum auction id
TOP_AUCTION_ID = 99999999999999

# Parameter plugin
PARAMETER_PLUGIN = RubiconPlugin

# RTB request template filename
TEMPLATE_FILENAME = 'templates/request.template'
