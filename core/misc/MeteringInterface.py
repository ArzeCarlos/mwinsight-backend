#MeteringInterface.py
from pydantic import BaseModel
from typing import Any
class MeteringPost(BaseModel):
    itemid: int
    data: Any
    latencia: float #Added


