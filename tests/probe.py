
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

def backup():
    cola = queue.Queue()
    colaresponse= queue.Queue()
    values=FetchData.get_items("https://mwinsight-backend.onrender.com/api/v1/items")
    values2=ItemMapper.mapItemItemstoItemArray(values["data"])
    # print(values2)
    for item in values2:
        if(item.enabled):
            # print(item.update_interval)
            queue_data={
                "id": item.id,
                "oid":item.snmp_oid,
                "ip": item.host.ip,
                "community": item.host.community    
            }
            cola.put(queue_data)
    # print(list(cola.queue))
    request= FetchData.dataSerialize(cola.get())
    SNMPCustomNumber.get_data(request,colaresponse)
    snmpresponse=colaresponse.get()
    if "error" not in snmpresponse:
        itemid=int(snmpresponse["itemid"])
        value=snmpresponse["channel"][0]["value"]
        data = ItemPut(id=itemid,latest_data=value)
        response=FetchData.put_item("https://mwinsight-backend.onrender.com/api/v1/items/",data=data)    
        print(response)
        response=FetchData.post_metering("https://mwinsight-backend.onrender.com/api/v1/meterings/",data=data)

def backup2():
    cola= queue.Queue()
    colaresponse= queue.Queue()
    interval:timedelta=timedelta(days=0,hours=0,seconds=60)
    running=True
    while running:
        responseFetch=FetchData.get_items("https://mwinsight-backend.onrender.com/api/v1/items")
        items=ItemMapper.mapItemItemstoItemArray(responseFetch["data"])
        # minUpdateValue=Helpers.MinUpdateValue(items)        
        minupdateinterval:timedelta=timedelta(days=0,hours=0,seconds=60)
        difference= timedelta(days=0,hours=0,seconds=2)
        for data in items:
            if(data.enabled):
                delta:timedelta=datetime.now()-data.updatedAt
                if(delta<minupdateinterval):
                    minupdateinterval=delta
                if(delta>data.update_interval):
                    queue_data={
                        "id": data.id,
                        "oid":data.snmp_oid,
                        "ip": data.host.ip,
                        "community": data.host.community    
                    }
                    cola.put(queue_data)    
        # interval=Helpers.SetInterval(minUpdateValue)
        interval=minupdateinterval-difference
        time.sleep(interval.seconds)

def fetcher_task(stop_event: threading.Event):
    """
    Este hilo se encarga de hacer polling del endpoint "items" y añadir a la cola
    aquellos items cuyo tiempo de actualización ha caducado. También se actualiza 
    el intervalo de polling con el valor mínimo de delta en cada iteración.
    """
    default_interval = timedelta(seconds=40)
    difference = timedelta(microseconds=20)
    
    while not stop_event.is_set():
        min_update_interval = default_interval

        response_fetch = FetchData.get_items("https://mwinsight-backend.onrender.com/api/v1/items")
        items = ItemMapper.mapItemItemstoItemArray(response_fetch["data"])
        print("Items obtenidos:", items)

        for item in items:
            if item.enabled:
                delta = datetime.now() - item.updatedAt  
                if delta < min_update_interval:
                    min_update_interval = delta
                if delta > item.update_interval or item.updatedAt==item.createdAt:
                    queue_data = {
                        "id": item.id,
                        "oid": item.snmp_oid,
                        "ip": item.host.ip,
                        "community": item.host.community    
                    }
                    cola.put(queue_data)

        interval_seconds = max(0.5, (min_update_interval - difference).total_seconds())
        time.sleep(interval_seconds)

def snmpers_task(stop_event: threading.Event):
    """
    Este hilo extrae peticiones desde la cola, realiza la consulta SNMP y actualiza el item 
    a través de los endpoints correspondientes.  
    """
    while not stop_event.is_set():
        try:
            request = FetchData.dataSerialize(cola.get(timeout=0.001))
        except queue.Empty:
            continue

        SNMPCustomNumber.get_data(request, colaresponse)
        
        try:
            snmp_response = colaresponse.get(timeout=0.001)
        except queue.Empty:
            continue
        
        if "error" not in snmp_response:
            item_id = int(snmp_response.get("itemid", 0))
            value = snmp_response["channel"][0]["value"]
            data_item = ItemPut(id=item_id, latest_data=value)
            
            response_put = FetchData.put_item("https://mwinsight-backend.onrender.com/api/v1/items/", data=data_item)
            response_post = FetchData.post_metering("https://mwinsight-backend.onrender.com/api/v1/meterings/", data=data_item)
        
        time.sleep(0.001)

def main():
    stop_event = threading.Event()
    
    # Creación y configuración de los hilos
    fetcher = threading.Thread(target=fetcher_task, args=(stop_event,), daemon=True)
    snmpers = threading.Thread(target=snmpers_task, args=(stop_event,), daemon=True)

    print("Iniciando fetcher...")
    fetcher.start()
    print("Iniciando snmpers...")
    snmpers.start()

    try:
        while fetcher.is_alive() and snmpers.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nDetectado Ctrl+C. Deteniendo hilos...")
        stop_event.set()
        fetcher.join()
        snmpers.join()
        print("Todos los hilos se han detenido correctamente.")

if __name__ == "__main__":
    main()

