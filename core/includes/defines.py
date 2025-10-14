"""
defines.py

2025 Carlos Arze
Trabajo de grado
Univalle

This script contains a collection of constants and definitions used throughout 
the project for managing thread types, network configurations,
and other system-wide settings.

"""

# URL fetch
ITEMS_URL="http://127.0.0.1:5000/api/v1/items/"
ITEMS_DATA_URL="http://127.0.0.1:5000/api/v1/items/monitoring"
METERINGS_URL= "http://127.0.0.1:5000/api/v1/meterings/"
# Available services
SNMP_FEATURE_STATUS = 'YES'  # Enables or disables SNMP feature
ICMP_FEATURE_STATUS = 'YES'  # Enables or disables ICMP feature

# Item types for monitoring
ITEM_TYPE_ICMP = 1  # ICMP monitoring type
ITEM_TYPE_SNMP = 2  # SNMP monitoring type

# Status values for operations
STATUS_OK = 'OK'  # Operation succeeded
STATUS_FAIL = 'FAIL'  # Operation failed

# Exit codes for threads
EXIT_SUCCESS = 0  # Indicates successful execution
EXIT_FAILURE = 1  # Indicates failure during execution

# Thread type identifiers (strings)
THREAD_TYPE_FETCHER = "FETCHER"  # FETCHER fetch thread
THREAD_TYPE_SNMPER = "SNMPER"  # SNMP polling thread

# Thread type enumerations (numeric)
THREAD_TYPE_FETCHER_VALUES = 0  # Thread type for PINGER
THREAD_TYPE_SNMPER_VALUES = 1  # Thread type for SNMPER
THREAD_TYPE_COUNT = 2  # Total number of different thread types
THREAD_TYPE_MAIN = 130  # Main thread identifier

# Critical error identifier
THIS_SHOULD_NEVER_HAPPEN = 101  # Used to signal a critical error that should not happen

# Log level identifiers for initial login
LOG_LEVEL_CRIT = 1  # Critical error level
LOG_LEVEL_ERR = 2  # Error level
LOG_LEVEL_WARNING = 3  # Warning level
LOG_LEVEL_TRACE = 4  # Debug level (also known as TRACE)
LOG_LEVEL_INFO = 5  # Info level
LOGGING_FILE = "./logs/network_monitor.log"  # Default log file path

# Port numbers for different services
DEFAULT_SERVER_PORT = 10000  # Port for the default server
SQL_SERVER_PORT = 3306  # Port for SQL server (MySQL)
HTTP_SERVER_PORT = 80  # HTTP server port
SNMP_QUERY_PORT = 161  # SNMP query port
VITE_PORT = 5173  # Vite development server port
FLASK_PORT = 5000  # Flask development server port

# Server flags status
SERVER_STOPPED = 1
SERVER_RUNNING = 0

# Number threads
NUM_FETCHERS = 1 #OK! 
NUM_SNMPERS = 2
