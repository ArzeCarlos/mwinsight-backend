#helpers.py
from datetime import timedelta
from typing import List
from .ItemInterface import Item

class Helpers(object):
    """Get the minimum update value from items"""
    @staticmethod
    def MinUpdateValue(items:List[Item]=[])->timedelta:
        if(items == []):
            return  "00:00:00"
        minvalue:timedelta=items[0].update_interval
        for data in range(len(items)):
            if items[data].update_interval < minvalue:
                minvalue = items[data].update_interval
        return minvalue
    def SetInterval(minUpdate: timedelta=timedelta(days=0,hours=0, seconds=10))->timedelta:
        difference= timedelta(days=0,hours=0,seconds=5)
        return  minUpdate-difference