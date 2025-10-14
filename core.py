"""
2025 Carlos Arze
Trabajo de grado
Univalle

This script is the core of the network monitoring system.
"""

from time import sleep
from queue import Queue
from threading import Event

from core.includes.defines import (
    DEFAULT_SERVER_PORT,
    LOGGING_FILE,
    THREAD_TYPE_FETCHER,
    SNMP_FEATURE_STATUS,
    ICMP_FEATURE_STATUS,
    STATUS_OK,
    SERVER_STOPPED,
    ITEMS_URL,
    ITEMS_DATA_URL,
    METERINGS_URL, THREAD_TYPE_SNMPER,
)
from core.config.utilities import Config
from core.config.logger import CustomLogger
from core.fetcher.fetcher_manager import FetcherManager
from core.snmper.snmper_manager import  SnmperManager

# Server metadata
title_message: str = "network_monitor_server"
version: str = "0.1.3"
revision: str = "1"

# Network config (TODO: load from file/env)
config_listen_ip: str = ""
config_listen_port: int = DEFAULT_SERVER_PORT

# Fetcher config
config_forks = {
    "FETCHERS": Config.get_thread_num(THREAD_TYPE_FETCHER),
    "SNMPERS": Config.get_thread_num(THREAD_TYPE_SNMPER),
}

# Intervals threads
interval_fetchers: float = 30.0
interval_snmper: float = 0.001

# Endpoints
items_url: str = ITEMS_URL
meterings_url: str = METERINGS_URL

# Shared resources
logger = CustomLogger(log_file=LOGGING_FILE)
task_fetcher_queue: Queue[dict] = Queue()
response_snmp_queue: Queue[dict] = Queue()
stop_event: Event = Event()

def load_config() -> list[dict]:
    """
    Load and validate server configuration parameters.
    Returns a list of dicts describing each parameter.
    """
    return [
        {
            "PARAMETER": "StartFetchers",
            "VAR": config_forks["FETCHERS"],
            "TYPE": "int",
            "MANDATORY": True,
            "MIN": 1,
            "MAX": 10,  # Test limit
        },
        {
            "PARAMETER": "StartSnmpers",
            "VAR": config_forks["SNMPERS"],
            "TYPE": "int",
            "MANDATORY": True,
            "MIN": 1,
            "MAX": 10,  # Test limit
        },
    ]

def on_exit() -> int:
    """
    Cleanup routine called when the server is stopping.
    Stops threads and logs final status.
    """
    logger.info("on_exit() called.")
    logger.info("Exiting server.")
    logger.info(f"({STATUS_OK}!) Server stopped. Project {version} (revision {revision}).")
    return SERVER_STOPPED

def server_startup() -> int:
    """
    Main startup routine for the server.
    Initializes logging, starts fetcher and SNMP threads, and waits for shutdown.
    """
    # Initial log messages
    logger.info("Server initialization complete.")
    logger.info(f"Starting Server. Project {version} (revision {revision}).")
    logger.info("****** Enabled features ******")
    logger.info(f"SNMP monitoring:  {SNMP_FEATURE_STATUS}")
    logger.info(f"ICMP monitoring:  {ICMP_FEATURE_STATUS}")
    logger.info(f"Number of fetchers:  {config_forks['FETCHERS']}")
    logger.info(f"Number of snmpers:  {config_forks['SNMPERS']}")
    logger.info("******************************")

    # Create and start fetcher threads
    manager_fetchers = FetcherManager(
        logger=logger,
        api_url=ITEMS_DATA_URL,
        task_queue=task_fetcher_queue,
        stop_event=stop_event,
        num_fetchers=config_forks["FETCHERS"],
        interval=interval_fetchers,
    )
    manager_fetchers.start_fetchers()
    logger.info("Fetcher threads started.")

    # Create and start SNMP threads
    manager_snmper = SnmperManager(
        logger=logger,
        api_url=items_url,
        task_queue=task_fetcher_queue,
        response_queue=response_snmp_queue,
        stop_event=stop_event,
        num_snmpers=config_forks["SNMPERS"],
        interval=interval_snmper,
    )
    manager_snmper.start_snmpers()
    logger.info("SNMP threads started.")

    # Main loop: wait until stopped or any threads die
    try:
        while (
            not stop_event.is_set()
            and manager_fetchers.all_fetchers_alive
            and manager_snmper.all_snmpers_alive
        ):
            sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping threads...")
        stop_event.set()
    finally:
        # Stop both sets of threads
        manager_snmper.stop_snmpers()
        manager_fetchers.stop_fetchers()
        return on_exit()


if __name__ == "__main__":
    exit_code = server_startup()
    exit(exit_code)
