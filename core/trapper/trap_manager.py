import threading
import asyncio
from pysnmp.carrier.asyncio.dispatch import AsyncioDispatcher
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.proto import api
from pyasn1.codec.ber import decoder

class TrapManager:
    """
    TrapManager basado en AsyncioDispatcher compatible con Windows y tu script de envío de traps.
    """

    def __init__(self, logger):
        self.logger = logger
        self.listeners = {}  # (host, port) -> {"oids": set(), "dispatcher": dispatcher}
        self.loop = asyncio.new_event_loop()
        self._loop_thread = None

    def _ensure_loop_running(self):
        if self._loop_thread and self._loop_thread.is_alive():
            return

        def run_loop():
            self.logger.info("[TrapManager] Loop asyncio iniciado en thread separado")
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()

    async def _start_listener_async(self, host, port):
        key = (host, port)
        if key in self.listeners:
            return

        dispatcher = AsyncioDispatcher()

        def trap_callback(dispatcher_, transport_domain, transport_address, wholeMsg):
            try:
                while wholeMsg:
                    msgVer = int(api.decodeMessageVersion(wholeMsg))
                    if msgVer not in api.PROTOCOL_MODULES:
                        self.logger.error(f"[TrapManager] Versión SNMP no soportada: {msgVer}")
                        return

                    pMod = api.PROTOCOL_MODULES[msgVer]
                    reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message())
                    pdu = pMod.apiMessage.get_pdu(reqMsg)

                    if pdu.isSameTypeWith(pMod.TrapPDU()) or pdu.isSameTypeWith(pMod.SNMPv2TrapPDU()):
                        varBinds = pMod.apiPDU.get_varbinds(pdu)
                        for oid, val in varBinds:
                            oid_str = oid.prettyPrint()
                            # Convertir cualquier valor a string de forma segura
                            if hasattr(val, 'prettyPrint'):
                                val_str = val.prettyPrint()
                            else:
                                val_str = str(val)

                            if oid_str in self.listeners[key]["oids"]:
                                self.logger.info(f"[TrapManager] Trap match {oid_str} recibido de {transport_address[0]}")
                                payload = {"ip": transport_address[0], "oid": oid_str, "valor": val_str, "tipo": 3}
                                print("Resultado trapper:", payload)
                            else:
                                self.logger.debug(f"[TrapManager] Trap ignorado OID={oid_str} no registrado")
            except Exception as e:
                self.logger.error(f"[TrapManager] Error procesando trap: {e}")

        dispatcher.register_recv_callback(trap_callback)
        dispatcher.register_transport(
            udp.DOMAIN_NAME,
            udp.UdpAsyncioTransport().open_server_mode((host, port))
        )

        dispatcher.job_started(1)
        self.listeners[key] = {"oids": set(), "dispatcher": dispatcher}
        self.logger.info(f"[TrapManager] Escuchando traps en {host}:{port}")

    def start_listener(self, host, port):
        self._ensure_loop_running()
        future = asyncio.run_coroutine_threadsafe(
            self._start_listener_async(host, port), self.loop
        )
        try:
            future.result(timeout=3)
        except Exception as e:
            self.logger.error(f"[TrapManager] No se pudo iniciar listener: {e}")

    def register_oid(self, host, port, oid):
        key = (host, port)
        if key not in self.listeners:
            self.logger.info(f"[TrapManager] Listener no existe para {host}:{port}, creando...")
            self.start_listener(host, port)

        self.listeners[key]["oids"].add(oid)
        self.logger.debug(f"[TrapManager] Registrado OID {oid} para {host}:{port}")
