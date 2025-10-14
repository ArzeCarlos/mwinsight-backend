#ItemMapper.py
from typing import Any, Dict, List
from .ItemInterface import Item,Host

class ItemMapper(object):
    @staticmethod
    def mapitemitemtoitem(data: Dict[str, Any]) -> Item:
        return Item(
            id=data["id"],
            name=data["name"],
            tipo=data["tipo"],
            snmp_oid=data["snmp_oid"],
            enabled=data["enabled"],
            update_interval=data["updateinterval"],
            factor_multiplicacion=data["factor_multiplicacion"],
            factor_division=data["factor_division"],
            updatedAt= data["updatedAt"],
            createdAt= data["createdAt"],
            host=Host(
            hostname=data["host"]["hostname"],
            ip=data["host"]["ip"],
            community=data["host"]["community"],
            )
        )
    @staticmethod    
    def mapitemitemstoitemarray(data_list: List[Dict[str, Any]]) -> List[Item]:
        itemmapper = ItemMapper()
        return [itemmapper.mapitemitemtoitem(item) for item in data_list]

