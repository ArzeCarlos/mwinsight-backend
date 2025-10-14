#ItemInterface.py
from pydantic import BaseModel
from datetime import timedelta,datetime
from typing import Any
class Host(BaseModel):
    hostname: str
    community: str
    ip: str

class Item(BaseModel):
    id: int
    name: str
    tipo: int
    factor_multiplicacion: int
    factor_division: int
    snmp_oid: str
    enabled: bool
    host: Host
    update_interval: timedelta
    updatedAt: datetime
    createdAt: datetime    
class ItemPut(BaseModel):
    id: int
    latest_data: Any

class ItemPutWithStatusCode(BaseModel):
    id: int
    status_codes: int
# Added latency
class MeteringPut(BaseModel):
    id: int
    latest_data: Any
    latencia: float
