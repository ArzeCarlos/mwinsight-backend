"""
fetcher_manager.py

2025 Carlos Arze
Trabajo de grado
Univalle

This script defines the Fetchermanager class, which is responsible for managing multiple fetcher threads.
The Fetchermanager starts, stops, and monitors the fetchers, including checking if they are still alive
and terminating them if necessary.
"""
from typing import List
from queue import Queue
from threading import Event
from .fetcher_thread import Fetcher
from ..config.logger import CustomLogger


class FetcherManager:
    """
    Class responsible for managing multiple fetcher threads. It starts, stops,
    and monitors fetchers, checking their status and letting them finish if necessary.
    """

    def __init__(self, logger: CustomLogger, api_url: str, task_queue: Queue, stop_event: Event, num_fetchers: int = 1,
                 interval: float = 10) -> None:
        self.logger = logger
        self.api_url = api_url
        self.num_fetchers = num_fetchers
        self.fetchers: List[Fetcher] = []
        self.task_queue = task_queue
        self.stop_event = stop_event
        self.interval = interval

    def _create_fetchers(self) -> Fetcher:
        """
        Factory method to create a fetcher with the specified configurations.

        Returns:
            Fetcher: A new fetcher instance.
        """
        return Fetcher(self.logger, self.api_url, self.task_queue, self.stop_event, self.interval)

    def start_fetchers(self) -> None:
        """
        Starts all the fetcher threads.

        This method initializes each fetcher and starts them.
        """
        self.logger.debug("Manager starting fetchers...")
        for _ in range(self.num_fetchers):
            fetcher = self._create_fetchers()
            self.fetchers.append(fetcher)
            fetcher.start()

    def stop_fetchers(self) -> None:
        """
        Stops all the fetcher threads.

        This method sets the stop event to signal the fetchers to stop,
        and then waits for each fetcher to finish.
        """
        self.stop_event.set()
        for fetcher in self.fetchers:
            fetcher.join(timeout=5)
            self.logger.debug(f"Fetcher-{fetcher.thread_id} stopped")
        self._terminate_if_alive()
        self.logger.debug("All fetchers have been stopped.")

    def _terminate_if_alive(self) -> None:
        """
        Verifies if the fetchers are still alive. If they are, waits for them to finish.

        This method joins any that are still alive.
        """
        for fetcher in self.fetchers:
            if fetcher.is_alive():
                self.logger.debug(f"Fetcher-{fetcher.thread_id} is still alive, waiting to finish...")
                fetcher.join()
                self.logger.debug(f"Fetcher-{fetcher.thread_id} has finished.")
            else:
                self.logger.debug(f"Fetcher-{fetcher.thread_id} was already stopped.")

    @property
    def all_fetchers_alive(self) -> bool:
        """
        Checks if all fetcher threads are currently alive.

        Returns:
            bool: True if all are alive, False otherwise.
        """
        return all(fetcher.is_alive() for fetcher in self.fetchers)

    @property
    def active_fetcher_ids(self) -> list:
        """
        Returns a list of thread IDs of active fetcher threads.

        Returns:
            list: thread identifiers of currently alive fetcher threads.
        """
        return [fetcher.thread_id for fetcher in self.fetchers if fetcher.is_alive()]
