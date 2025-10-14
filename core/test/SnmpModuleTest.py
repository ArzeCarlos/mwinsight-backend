
from checkers.snmp.snmpnumber import SNMPCustomNumber
from queue import Queue

class testSnmp(object):
    """ Tester snmp numerical values."""
    @staticmethod
    def testSnmpModule(oid: str='1.3.6.1.2.1',host: str='localhost',value_type: str="1"
                       ,community: str="public",port: int=161, unit: str="",multiplication: int=1
                       ,division: int=1,itemid: int=1)->None:
        print("Starting application...")
        data_queue = Queue()
        data = {
            'oid': oid,
            'host': host,
            'value_type': value_type,
            'community': community,
            'port': port,
            'unit': unit,
            'multiplication': multiplication,
            'division': division,
            'itemid': itemid
        }
        print(data)
        try:
            # SNMPCustomNumber.get_data(data, data_queue)
            response=SNMPCustomNumber.get_data(data)
            print("Data retrieved from query:", response)
        except Exception as e:
            print("An error occurred:", e)
