"""
fetcher_thread.py

2025 Carlos Arze
Trabajo de grado
Univalle

This script is the definition of the fetcher thread. This module is responsible for
    fetching data request form active hosts and placing them in the queue.
"""
from time import monotonic
from datetime import datetime, timedelta
from queue import Queue
import socket 
from threading import Thread, Event, get_ident
from typing import Optional, Dict, List, Any
import pymysql
from ..config.logger import CustomLogger
from ..includes import defines as defines
from ..misc.fetch_data import FetchData
from ..misc.ItemMapper import ItemMapper
from ..misc.ItemInterface import Item



class Fetcher(Thread):
    """
    Class representing a fetcher thread. This thread fetches the list host data request
    from an API and places each request into a queue to be processed by other threads.
    """

    def __init__(self, logger: CustomLogger, api_url: str, task_queue: Queue, stop_event: Event, interval: float = 30 ) -> None:
        """
        Initializes the fetcher threads.

        Args:
            logger (CustomLogger): Custom logger instance for logging events.
            api_url (str): The URL of the API from which the request data hosts are fetched.
            task_queue (Queue): The queue where items data will be placed for processing.
            interval (float): The interval in seconds for making the task. Default is 30.
            stop_event (Event): Event that signals when to stop the thread. Default is None.
        """
        super().__init__()
        self.api_url = api_url
        self.task_queue = task_queue
        self.interval = interval
        self.stop_event = stop_event
        self.logger = logger
        self.thread_id: Optional[int] = None
        self.last_enqueued: dict[int, datetime] = {} #Third approach
        self.wake_event = Event() #Signal new values(Last approach)
    
    def _fetch_data(self, api_url: str) -> List[Item]:
        """
        Fetches the list of request data (items) hosts from the API.

        Args:
            api_url (str): The URL of the API from which items are fetchednext_interval.

        Returns:
        List[Item]: A list of Item objects if the API request is successful,
                              or None if the request fails or no data is returned.
        """
        self.logger.debug(f"[Fetcher-{self.thread_id}] Fetching items from {api_url}")
        response_fetch: Optional[Dict] = FetchData.get_items(self.api_url)
        if response_fetch:
            # items: List[Item] = ItemMapper.mapitemitemstoitemarray(response_fetch["data"])
            items: List[Item] = ItemMapper.mapitemitemstoitemarray(response_fetch)
            self.logger.debug(f"[Fetcher-{self.thread_id}] Retrieved {len(items)} items")
            return items
        else:
            self.logger.error(f"[Fetcher-{self.thread_id}] Error fetching items from {api_url}")
            return []
    
    def run(self) -> None:
        # self._run_approach1()
        # self._run_approach2()
        # self._run_approach3()
        self._start_wake_server()
        self._run_approach4()

    def _run_approach1(self)-> None:
        """
        Main fetcher thread. Each iteration:
          - Calls self._fetch_data()
          - Enqueues items whose update interval has expired or that are just created.
          - Sleeps exactly until the next due update, compensating for processing latency.
        Loop exits when self.stop_event is set.
        """
        self.thread_id = get_ident()
        self.logger.info(f"[Fetcher-{self.thread_id}] Thread started")

        default_interval: float = self.interval
        latency_compensation: float = timedelta(microseconds=20).total_seconds()
        creation_threshold: timedelta = timedelta(microseconds=20)

        while not self.stop_event.is_set():
            start_monotonic: float = monotonic()
            next_interval: float = default_interval

            items: List[Item] = self._fetch_data(self.api_url)

            next_intervals: List[float] = []
            for item in items:
                if not item.enabled:
                    continue

                due_time: datetime = item.updatedAt + item.update_interval
                delay: float = (due_time - datetime.now()).total_seconds()

                if delay <= 0 or abs(item.updatedAt - item.createdAt) <= creation_threshold:
                    payload: Dict[str, Any] = {
                        "id": item.id,
                        "oid": item.snmp_oid,
                        "ip": item.host.ip,
                        "community": item.host.community,
                        "tipo": item.tipo,
                        "factor_division": item.factor_division,
                        "factor_multiplicacion": item.factor_multiplicacion
                    }
                    self.task_queue.put(payload)
                    self.logger.debug(f"[Fetcher-{self.thread_id}] Enqueued item {item.id} for SNMP check")
                    delay = item.update_interval.total_seconds()

                if item.tipo != 3:
                    next_intervals.append(delay)

            if next_intervals:
                next_interval = max(0.1, min(next_intervals) - latency_compensation)

            elapsed: float = monotonic() - start_monotonic
            timeout: float = max(0.0, next_interval - elapsed)
            self.stop_event.wait(timeout=timeout)

        self.logger.info(f"[Fetcher-{self.thread_id}] Thread stopped")

    def _run_approach2(self)-> None:
        self.thread_id = get_ident()
        self.logger.info(f"[Fetcher-{self.thread_id}] Thread started")
        default_interval: float = self.interval
        while not self.stop_event.is_set():
            start_monotonic: float = monotonic()
            conn = pymysql.connect(
                host="127.0.0.1",
                user="root",
                password="carlos",
                database="bdnetworkmonitoring",
                cursorclass=pymysql.cursors.DictCursor
            )
            try:
                with conn.cursor() as cur:
                    sql_min = """
                        SELECT MIN(updateinterval) AS min_interval
                        FROM items
                        WHERE ADDTIME(updatedAt, updateinterval) <= CURRENT_TIMESTAMP()
                        AND enabled = TRUE;
                    """
                    cur.execute(sql_min)
                    row = cur.fetchone()               
                    min_interval = row["min_interval"]
                    if min_interval is None:
                        print("No hay ítems pendientes")
                    else:
                        total_sec = int(min_interval.total_seconds())
                        print(f"Mínimo intervalo: {total_sec} s")
                    sql_items = """
                        SELECT
                            i.id,
                            i.snmp_oid      AS oid,
                            h.ip,
                            h.community,
                            i.tipo,
                            i.enabled
                        FROM items i
                        JOIN hosts h ON i.hostid = h.id
                        WHERE ADDTIME(i.updatedAt, i.updateinterval) <= CURRENT_TIMESTAMP()
                        AND i.enabled = TRUE;
                    """
                    cur.execute(sql_items)
                    items = cur.fetchall()
            finally:
                    conn.close()            
                    # items: List[Item] = self._fetch_data_approach2(self.api_url, itemstocheck="ok")
                    for item in items:
                        if item["enabled"]:
                            print(item['id'])
                        payload: Dict[str, Any] = {
                            "id": item["id"],
                            "oid": item["oid"],
                            "ip": item["ip"],
                            "community": item["community"],
                            "tipo": item["tipo"]
                        }
                        self.task_queue.put(payload)
                        self.logger.debug(f"[Fetcher-{self.thread_id}] Enqueued item {item['id']} for SNMP check")
                    elapsed: float = monotonic() - start_monotonic
                    timeout: float = max(0.0,total_sec)
                    self.stop_event.wait(timeout=timeout)

            # self.logger.info(f"[Fetcher-{self.thread_id}] Thread stopped")
    def _run_approach3(self) -> None:
        """
            Main fetcher thread with deduplication.
            Each iteration:
            - Calls self._fetch_data()
            - Enqueues items only if:
                1. Update interval has expired, AND
                2. The updatedAt is newer than the last time it was enqueued, OR it's just created
            - Sleeps until the next due update, compensating for processing latency.
            Loop exits when self.stop_event is set.
        """
        self.thread_id = get_ident()
        self.logger.info(f"[Fetcher-{self.thread_id}] Thread started")

        default_interval: float = self.interval
        latency_compensation: float = timedelta(microseconds=20).total_seconds()
        creation_threshold: timedelta = timedelta(microseconds=20)

        while not self.stop_event.is_set():
            start_monotonic: float = monotonic()
            next_interval: float = default_interval

            items: List[Item] = self._fetch_data(self.api_url)

            next_intervals: List[float] = []
            for item in items:
                if not item.enabled:
                    continue

                due_time: datetime = item.updatedAt + item.update_interval
                delay: float = (due_time - datetime.now()).total_seconds()

                last_time = self.last_enqueued.get(item.id)

                if (
                    delay <= 0
                    and (last_time is None or item.updatedAt > last_time)
                ) or abs(item.updatedAt - item.createdAt) <= creation_threshold:
                    payload: Dict[str, Any] = {
                        "id": item.id,
                        "oid": item.snmp_oid,
                        "ip": item.host.ip,
                        "community": item.host.community,
                        "tipo": getattr(item, "tipo", None),
                        "factor_division": getattr(item, "factor_division", 1),
                        "factor_multiplicacion": getattr(item, "factor_multiplicacion", 1),
                    }
                    self.task_queue.put(payload)
                    self.logger.debug(
                        f"[Fetcher-{self.thread_id}] Enqueued item {item.id} for SNMP check"
                    )
                    self.last_enqueued[item.id] = item.updatedAt
                    delay = item.update_interval.total_seconds()

                next_intervals.append(delay)

            if next_intervals:
                next_interval = max(0.1, min(next_intervals) - latency_compensation)

            elapsed: float = monotonic() - start_monotonic
            timeout: float = max(0.0, next_interval - elapsed)
            self.stop_event.wait(timeout=timeout)

        self.logger.info(f"[Fetcher-{self.thread_id}] Thread stopped")

    #Handler new values(Last approach)
    def _start_wake_server(self):
        """Servidor TCP para recibir señal de despertar desde otro proceso/script."""
        def server():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', 5050))  # Cambiar puerto(si es necesario)
                s.listen(1)
                while not self.stop_event.is_set():
                    try:
                        conn, _ = s.accept()
                        with conn:
                            data = conn.recv(16)
                            if data == b"WAKE":
                                self.logger.info(f"[Fetcher-{self.thread_id}] Wake signal received")
                                self.wake_event.set()
                    except Exception as e:
                        self.logger.error(f"[Fetcher-{self.thread_id}] Wake server error: {e}")
        Thread(target=server, daemon=True).start()
    def _run_approach4(self) -> None:
        """
        Main fetcher thread with deduplication and external wake-up support.
        
        Variaciones respecto a _run_approach3:
        1. Se espera en self.wake_event además de stop_event.
        2. Se resetea self.wake_event después de cada despertar para el próximo ciclo.
        3. Permite que un proceso externo despierte inmediatamente el fetcher.
        """
        self.thread_id = get_ident()
        self.logger.info(f"[Fetcher-{self.thread_id}] Thread started")

        default_interval: float = self.interval
        latency_compensation: float = timedelta(microseconds=20).total_seconds()
        creation_threshold: timedelta = timedelta(microseconds=20)

        while not self.stop_event.is_set():
            start_monotonic: float = monotonic()
            next_interval: float = default_interval

            items: List[Item] = self._fetch_data(self.api_url)

            next_intervals: List[float] = []
            for item in items:
                if not item.enabled:
                    continue

                due_time: datetime = item.updatedAt + item.update_interval
                delay: float = (due_time - datetime.now()).total_seconds()

                last_time = self.last_enqueued.get(item.id)

                if (
                    delay <= 0
                    and (last_time is None or item.updatedAt > last_time)
                ) or abs(item.updatedAt - item.createdAt) <= creation_threshold:
                    payload: Dict[str, Any] = {
                        "id": item.id,
                        "oid": item.snmp_oid,
                        "ip": item.host.ip,
                        "community": item.host.community,
                        "tipo": getattr(item, "tipo", None),
                        "factor_division": getattr(item, "factor_division", 1),
                        "factor_multiplicacion": getattr(item, "factor_multiplicacion", 1),
                    }
                    self.task_queue.put(payload)
                    self.logger.debug(f"[Fetcher-{self.thread_id}] Enqueued item {item.id} for SNMP check")
                    self.last_enqueued[item.id] = item.updatedAt
                    delay = item.update_interval.total_seconds()

                next_intervals.append(delay)

            if next_intervals:
                next_interval = max(0.1, min(next_intervals) - latency_compensation)

            elapsed: float = monotonic() - start_monotonic
            timeout: float = max(0.0, next_interval - elapsed)

            # =============================
            # Diferencia principal respecto a _run_approach3:
            # 1. Se usa self.wake_event para permitir despertar el fetcher desde otro proceso.
            # 2. self.wake_event.wait(timeout) reemplaza el sleep normal.
            # 3. Luego de despertar, se limpia el evento para el próximo ciclo.
            # =============================
            self.wake_event.wait(timeout=timeout)  # Espera timeout o señal de wake_event
            self.wake_event.clear()  # Resetea el evento

        self.logger.info(f"[Fetcher-{self.thread_id}] Thread stopped")

    def stop(self) -> None:
        """
        Stops the fetcher thread by setting the stop event.

        Logs that the fetcher thread is stopping, including its thread ID.
        """
        if self.thread_id is None:
            self.logger.warning("[Fetcher-?] Attempted to stop a fetcher thread before it started.")
        else:
            self.logger.info(f"[Fetcher-{self.thread_id}] Stopping thread.")
        self.stop_event.set()
