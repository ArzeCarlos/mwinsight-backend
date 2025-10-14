"""
snmper_manager.py

2025 Carlos Arze
Trabajo de grado
Univalle

This script defines the Snmpermanager class, which is responsible for managing multiple snmper threads.
The Snmpermanager starts, stops, and monitors the snmpers, including checking if they are still alive
and terminating them if necessary.
"""
from typing import List
from queue import Queue
from threading import Event
from .snmper_thread import Snmper
from ..config.logger import CustomLogger


class SnmperManager:
    """
    Class responsible for managing multiple snmper threads. It starts, stops,
    and monitors snmpers, checking their status and letting them finish if necessary.
    """

    def __init__(self, logger: CustomLogger, api_url: str, task_queue: Queue, response_queue: Queue, stop_event: Event,
                 num_snmpers: int = 1, interval: float = 0.001) -> None:
        self.logger = logger
        self.api_url = api_url
        self.num_snmpers = num_snmpers
        self.snmpers: List[Snmper] = []
        self.task_queue = task_queue
        self.response_queue= response_queue
        self.stop_event = stop_event
        self.interval = interval

    def _create_snmpers(self) -> Snmper:
        """
        Factory method to create a snmper with the specified configurations.

        Returns:
            Snmper: A new snmper instance.
        """
        return Snmper(self.logger, self.api_url, self.task_queue, self.response_queue, self.stop_event, self.interval)

    def start_snmpers(self) -> None:
        """
        Starts all the snmper threads.

        This method initializes each snmper and starts them.
        """
        self.logger.debug("Manager starting snmpers...")
        for _ in range(self.num_snmpers):
            snmper = self._create_snmpers()
            self.snmpers.append(snmper)
            snmper.start()

    def stop_snmpers(self) -> None:
        """
        Stops all the snmper threads.

        This method sets the stop event to signal the snmpers to stop,
        and then waits for each snmper to finish.
        """
        self.stop_event.set()
        for snmper in self.snmpers:
            snmper.join(timeout=5)
            self.logger.debug(f"Snmper-{snmper.thread_id} stopped")
        self._terminate_if_alive()
        self.logger.debug("All snmpers have been stopped.")

    def _terminate_if_alive(self) -> None:
        """
        Verifies if the snmpers are still alive. If they are, waits for them to finish.

        This method joins any that are still alive.
        """
        for snmper in self.snmpers:
            if snmper.is_alive():
                self.logger.debug(f"Snmper-{snmper.thread_id} is still alive, waiting to finish...")
                snmper.join()
                self.logger.debug(f"Snmper-{snmper.thread_id} has finished.")
            else:
                self.logger.debug(f"Snmper-{snmper.thread_id} was already stopped.")

    @property
    def all_snmpers_alive(self) -> bool:
        """
        Checks if all snmper threads are currently alive.

        Returns:
            bool: True if all are alive, False otherwise.
        """
        return all(snmper.is_alive() for snmper in self.snmpers)

    @property
    def active_snmper_ids(self) -> list:
        """
        Returns a list of thread IDs of active snmper threads.

        Returns:
            list: thread identifiers of currently alive snmper threads.
        """
        return [snmper.thread_id for snmper in self.snmpers if snmper.is_alive()]
