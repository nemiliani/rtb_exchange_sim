import logging

# Plugin imports
from plugin.rubicon_plugin import RubiconPlugin
from plugin.datacratic_plugin import DatacraticPlugin

# Max connections for bid requests allowed for the process
MAX_CONNS = 100
# Amount of connections for event notification allowed for the process
MAX_EVENT_CONNS = 10

# Endpoint list containing tuples for the DSPs (endpoint, expected_qps) where :
#  - endpoint should be a string 'host:port'
#  - expected_qps is the amount of qps expected for the endpoint
ENDPOINT_LIST = [
    ('localhost:80', 1),
]

# Event endpoint :
# - endpoint should be a string 'host:port'
EVENT_ENDPOINT = 'localhost:9876'

# Balance time out indicating the period in seconds 
# to balance connections
BALANCE_TO = 3

# Check connections time out indicating the period in
# seconds to verify if a connection attempt was successfull
CHECK_CONNS_TO = 1

# Check pending wins and try to send them
CHECK_PENDING_TO = 1

# Keep alive time out for the event conns in seconds, if no
# keep alive need to be sent set it to None 
EVENT_CONN_KEEP_ALIVE_TO = None

# Keep alive request
KEEP_ALIVE_HTTP_REQUEST = \
    'GET / HTTP/1.1\r\n' \
    'Keep-Alive: timeout=%d, max=5000\r\n' \
    'Connection: Keep-Alive\r\n' 

# Log level should be one of :
# - logging.DEBUG
# - logging.INFO
# - logging.WARNING
# - logging.ERROR
LOG_LEVEL = logging.DEBUG

# Parameter plugin
PARAMETER_PLUGIN = RubiconPlugin

# RTB request template filename
TEMPLATE_FILENAME = 'templates/request.template'
