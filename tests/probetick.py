import queue
import time
import threading
from core.misc.ItemMapper import ItemMapper
from core.checkers.snmp.snmpnumber import SNMPCustomNumber 
from core.misc.fetch_data import FetchData
from core.misc.ItemInterface import ItemPut
# from core.misc.helpers import Helpers
from datetime import datetime,timedelta
cola= queue.Queue()
colaresponse= queue.Queue()


def fetcher_task(stop_event: threading.Event):
    """
    Hilo encargado de:
      - Hacer polling del endpoint "items".
      - Calcular para cada ítem el tiempo exacto de actualización basado en su timestamp 'updatedAt' 
        y 'update_interval'.
      - Añadir a la cola aquellos ítems cuyo tiempo de actualización ya se venció.
      - Calcular un delay preciso para el siguiente ciclo considerando la latencia en procesamiento.
    """
    # Intervalo por defecto en caso de no hallar ítems
    default_interval = timedelta(seconds=40)
    # Diferencia para compensar la latencia
    difference = timedelta(microseconds=20)
    umbral = timedelta(microseconds=20)
    while not stop_event.is_set():
        start_monotonic = time.monotonic()
        
        # Se consulta el endpoint para obtener la lista de items
        response_fetch = FetchData.get_items("https://mwinsight-backend.onrender.com/api/v1/items")
        items = ItemMapper.mapItemItemstoItemArray(response_fetch["data"])
        print("Items obtenidos:", items)

        # Lista para almacenar el tiempo (en segundos) restante para la próxima actualización de cada item
        next_intervals = []
        for item in items:
            if item.enabled:
                # Se calcula el siguiente tiempo en que se debe actualizar el ítem
                next_update_time = item.updatedAt + item.update_interval
                delay = (next_update_time - datetime.now()).total_seconds()
                if delay <= 0 or abs(item.updatedAt - item.createdAt) <= umbral:
                    # Si ya venció el intervalo, se envía la petición inmediatamente
                    queue_data = {
                        "id": item.id,
                        "oid": item.snmp_oid,
                        "ip": item.host.ip,
                        "community": item.host.community    
                    }
                    print(queue_data)
                    cola.put(queue_data)
                    # Para el próximo ciclo, se asume que se reinicia el contador del update_interval
                    delay = item.update_interval.total_seconds()
                next_intervals.append(delay)

        # Se calcula el delay mínimo entre todos los ítems (con un mínimo para evitar un 0 o muy corto)
        if next_intervals:
            # Se compensa el tiempo de diferencia
            next_interval = max(0.1, min(next_intervals) - difference.total_seconds())
        else:
            next_interval = default_interval.total_seconds()

        # Se mide el tiempo ya consumido en la iteración y se ajusta el timeout
        elapsed = time.monotonic() - start_monotonic
        timeout = max(0, next_interval - elapsed)
        
        # Se espera el tiempo calculado o hasta que se active el stop_event
        stop_event.wait(timeout=timeout)

def snmpers_task(stop_event: threading.Event):
    """
    Hilo encargado de:
      - Extraer peticiones de la cola.
      - Realizar consultas SNMP.
      - Actualizar el item a través de los endpoints correspondientes (PUT y POST).
    """
    while not stop_event.is_set():
        try:
            request = FetchData.data_serialize(cola.get(timeout=1))
            print(request)
        except queue.Empty:
            continue

        # Realiza la consulta SNMP y coloca la respuesta en 'colaresponse'
        SNMPCustomNumber.get_data(request, colaresponse)
        
        try:
            snmp_response = colaresponse.get(timeout=1)
        except queue.Empty:
            continue
        
        if "error" not in snmp_response:
            item_id = int(snmp_response.get("itemid", 0))
            value = snmp_response["channel"][0]["value"]
            data_item = ItemPut(id=item_id, latest_data=value)
            
            # Se actualiza el item y se reporta el metering correspondiente
            response_put = FetchData.put_item("https://mwinsight-backend.onrender.com/api/v1/items/", data=data_item)
            response_post = FetchData.post_metering("https://mwinsight-backend.onrender.com/api/v1/meterings/", data=data_item)
        
        # Se minimiza la espera para continuar el ciclo sin bloqueos
        time.sleep(0.001)

def main():
    stop_event = threading.Event()
    
    # Inicialización de colas compartidas para las tareas
    global cola, colaresponse
    cola = queue.Queue()
    colaresponse = queue.Queue()
    
    # Creación de hilos
    fetcher = threading.Thread(target=fetcher_task, args=(stop_event,), daemon=True)
    snmpers = threading.Thread(target=snmpers_task, args=(stop_event,), daemon=True)

    print("Iniciando fetcher...")
    fetcher.start()
    print("Iniciando snmpers...")
    snmpers.start()

    try:
        # Ciclo activo para mantener el main en ejecución mientras los hilos están activos.
        while fetcher.is_alive() and snmpers.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nDetectado Ctrl+C. Deteniendo hilos...")
        stop_event.set()
        fetcher.join()
        snmpers.join()
        print("Todos los hilos se han detenido correctamente.")

if __name__ == '__main__':
    main()
