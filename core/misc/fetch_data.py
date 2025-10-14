import requests
from typing import Optional,Dict
from .ItemInterface import ItemPut, ItemPutWithStatusCode
from .MeteringInterface import MeteringPost
class FetchData(object):
    @staticmethod
    def get_items(url: str):
        try:
            response= requests.get(url)
            response_json=response.json()
            return response_json
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None
    @staticmethod
    def get_items_params(url: str, **params):
        try:
            response = requests.get(url, params=params or None)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None
    @staticmethod
    def serializer_snmp(data: dict)-> dict:
        return ({
            'oid':data["oid"],
            'host':data["ip"],
            'value_type':data["tipo"],
            'community':data["community"],
            'port': 161, ##Esto es 1611 para testing
            'unit': "°C",
            'multiplication': data["factor_multiplicacion"],
            'division': data["factor_division"],
            'itemid': data["id"]
        })
    @staticmethod
    def serializer_icmp(data: dict)-> dict:
        return ({
            'host': data["ip"],
            'value_type': data["tipo"],
            'pingcount': 4,
            'timeout': 30,
            'packsize': 100,
            'itemid': data["id"]
        })

    @staticmethod
    def put_item(url: str, data: ItemPut) -> Optional[Dict]:
        try:
            full_url = f"{url}{data.id}"
            payload = {"latest_data": data.latest_data}
            response = requests.put(full_url, json=payload)
            response.raise_for_status()  
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[PutItem] An error occurred: {e}")
            return None
    @staticmethod
    def put_item_status_code(url:str, data: ItemPutWithStatusCode)-> Optional[Dict]:
        try:
            full_url = f"{url}{data.id}"
            payload = {"status_codes": data.status_codes}
            response = requests.put(full_url, json=payload)
            response.raise_for_status()  
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[PutItemWithStatusCode] An error occurred: {e}")
            return None
    @staticmethod
    def post_metering(url:str, data: MeteringPost)-> Optional[Dict]:
        try:
            full_url = f"{url}"
            payload = {"itemid": data.id,
                       "valor": data.latest_data,
                       "latencia": data.latencia} #Added latency
            response = requests.post(full_url, json=payload)
            response.raise_for_status()  
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[PostMetering] An error occurred: {e}")
            return None
    @staticmethod
    def post_snmp_failures(url: str, data: Dict)-> Optional[Dict]:
        try:
            full_url = url
            payload = {'itemid': data['itemid'],
                       'host_ip': data['ip'],
                       'oid': data['oid'],
                       'mensaje': data['mensaje'],
                       "valor": data['valor']}
            response = requests.post(full_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f'[PostSNMPFailure] An error ocurred: {e}')
            return None