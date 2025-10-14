"""
snmper_thread.py

2025 Carlos Arze
Trabajo de grado
Univalle

This script is the definition of the snmper thread. This module is responsible for
    get item from task_queue, make snmpget and put the result in response_queue
"""
from time import sleep
from queue import Queue, Empty
from threading import Thread, Event, get_ident
from typing import Optional, Dict, List

from core.trapper.trap_manager import TrapManager

from ..config.logger import CustomLogger
from ..includes.defines import ITEMS_URL, METERINGS_URL
from ..misc.fetch_data import FetchData
from ..checkers.snmp.snmpnumber import SNMPCustomNumber
from ..checkers.ping import Ping
from ..misc.ItemInterface import ItemPut, ItemPutWithStatusCode, MeteringPut


class Snmper(Thread):
    """
    Class representing a snmper thread. This thread gets items from task_queue,
    makes SNMP GET requests and puts the results in response_queue.
    """

    def __init__(
        self,
        logger: CustomLogger,
        api_url: str,
        task_queue: Queue,
        response_queue: Queue,
        stop_event: Event,
        interval: float = 0.001
    ) -> None:
        """
        Initializes the snmper thread.

        Args:
            logger (CustomLogger): Custom logger instance for logging events.
            api_url (str): The URL of the API for item definitions.
            task_queue (Queue): Queue where items data is placed for processing.
            response_queue (Queue): Queue where SNMP results are placed.
            stop_event (Event): Event signaling when to stop the thread.
            interval (float): Minimal sleep interval between iterations. Default is 0.001s.
        """
        super().__init__()
        self.api_url = api_url
        self.task_queue = task_queue
        self.response_queue = response_queue
        self.interval = interval
        self.stop_event = stop_event
        self.logger = logger
        self.thread_id: Optional[int] = None
        self.trap_manager = TrapManager(logger)
    def _data_serialize(self, task_queue: Queue) -> Dict:
        """
        Retrieves and formats the next item from the task_queue.

        Args:
            task_queue (Queue): The queue from which to get raw item data.

        Returns:
            Dict: Formatted data dict for SNMP GET.
        """
        # self.logger.debug(f"[Snmper-{self.thread_id}] Waiting for data in queue...")
        raw = task_queue.get(timeout=1)
        self.logger.debug(f"[Snmper-{self.thread_id}] Items data: {raw}")
        data_formated: Dict ={}
        if raw["tipo"]==1 or raw['tipo']==3: #SNMP
            data_formated= FetchData.serializer_snmp(raw)
        elif raw["tipo"]==2: #ICMP
            data_formated= FetchData.serializer_icmp(raw)
        # self.logger.debug(f"[Snmper-{self.thread_id}] Serialized data: {snmp_data_formated}")
        return data_formated

    def run(self) -> None:
        """
        Main snmper thread loop:
          - Fetch and format items from task_queue.
          - Execute SNMP GET and wait for response.
          - Update item data via API and post metering if successful.
        Loop exits when stop_event is set.
        """
        self.thread_id = get_ident()
        self.logger.info(f"[Snmper-{self.thread_id}] Thread started.")

        while not self.stop_event.is_set():
            try:
                item_formated = self._data_serialize(self.task_queue)
            except Empty:
                continue
            # self.logger.debug(f"[Snmper-{self.thread_id}] Sending SNMP request for item {item_formatted.get('itemid')}")
            if item_formated["value_type"]==1: ## SNMP
                snmp_response: Dict = SNMPCustomNumber.get_data(item_formated)
                if "error" not in snmp_response  and "channel" in snmp_response and snmp_response["channel"][0]["value"] is not None:
                    item_id = int(snmp_response.get("itemid", 0))
                    value = snmp_response["channel"][0]["value"]
                    latencia_v = snmp_response["channel"][1]["value"] #Added
                    data_item = ItemPut(id=item_id, latest_data=value)
                    data_item_metering = MeteringPut(id=item_id, latest_data=value, latencia=latencia_v)
                    self.logger.debug(f"[Snmper-{self.thread_id}] SNMP result for item {item_id}: {value}")

                    response_put: Optional[Dict] = FetchData.put_item(ITEMS_URL, data=data_item)
                    # Latency added
                    response_post: Optional[Dict] = FetchData.post_metering(METERINGS_URL, data=data_item_metering)

                    if response_put and response_post:
                        self.logger.info(f"[Snmper-{self.thread_id}] Successfully inserted data for item ID {item_id}.")
                    else:
                        self.logger.error(
                            f"[Snmper-{self.thread_id}] Failed to insert data for item ID {item_id}. "
                            f"PUT response: {response_put}, POST response: {response_post}"
                        )
                else:
                    data = {
                        'itemid':snmp_response['itemid'],
                        'ip':item_formated['host'],
                        'oid':item_formated['oid'],
                        'mensaje':'No se recibió respuesta SNMP antes de que se agotara el tiempo de espera.',
                        'valor':'',
                    }

                    # dirty trick(Change new versions)
                    data_item = ItemPut(id=snmp_response['itemid'], latest_data=0)
                    response_put: Optional[Dict] = FetchData.put_item(ITEMS_URL, data=data_item)

                    # Need migrate db
                    # data_item = ItemPutWithStatusCode(id=snmp_response['itemid'], status_codes=456)
                    # response_put: Optional[Dict] = FetchData.put_item_status_code(ITEMS_URL, data=data_item)
                    
                    response_post_snmp_failed: Optional[Dict] =  FetchData.post_snmp_failures('http://127.0.0.1:5000/api/v1/meterings/falla',data)
                    self.logger.error(
                        f"[Snmper-{self.thread_id}] SNMP error for item {snmp_response['itemid']}: {snmp_response['channel'][0].get('error')}"
                    )

            elif item_formated["value_type"]==2: ## ICMP
                ping_response: Dict = Ping.get_data(item_formated)
                if "error" in ping_response:
                    ## Insert in table for alerts.
                    print("generar alerta")
                else:
                    print("insertar en item ok!")
            elif item_formated["value_type"]==3: ##Trap
                self.handle_trap(item_formated)
            # try:
            #     ping_response: Dict = self.response_queue.get(timeout=1)
            # except Empty:
            #     # self.logger.warning(f"[Snmper-{self.thread_id}] No SNMP response received (timeout).")
            #     continue

            sleep(self.interval)

        self.logger.info(f"[Snmper-{self.thread_id}] Thread exiting.")

    def stop(self) -> None:
        """
        Stops the snmper thread by setting the stop event.

        Logs that the snmper thread is stopping, including its thread ID.
        """
        if self.thread_id is None:
            self.logger.warning("[Snmper-?] Attempted to stop a snmper thread before it started.")
        else:
            self.logger.info(f"[Snmper-{self.thread_id}] Stopping thread.")
        self.stop_event.set()

    def handle_trap(self, item: Dict):
        ip = item["host"]
        oid = item["oid"]
        
        port = 1165 if ip in ("localhost", "127.0.0.1") else 162

        key = (ip, port)

        self.logger.debug(f"[Snmper-{self.thread_id}] Manejo de trap para {ip}:{port} y OID {oid}")

        try:
            if key not in self.trap_manager.listeners:
                self.logger.debug(f"[Snmper-{self.thread_id}] Listener no existe, arrancando...")
                self.trap_manager.start_listener(ip, port)

            if oid not in self.trap_manager.listeners[key]["oids"]:
                self.trap_manager.register_oid(ip, port, oid)
            else:
                self.logger.debug(f"[Snmper-{self.thread_id}] OID {oid} ya registrado para {ip}:{port}")

        except Exception as e:
            self.logger.error(f"[Snmper-{self.thread_id}] Error registrando trap: {e}")
