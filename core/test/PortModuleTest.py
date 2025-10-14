from checkers.port import Port
from queue import Queue

class testPort(object):
    @staticmethod
    def testPortModule(host: str='localhost',targetport:int=22,timeout: float=1
                       ,itemid:int=1)->None:
        print("Starting application...")
        data_queue = Queue()
        data = {
            'host': host,   
            'targetport': targetport,
            'timeout': timeout,
            'sensorid': itemid,
        }
        try:
            Port.get_data(data, data_queue)
            print("Data retrieved from queue:", data_queue.get())
        except Exception as e:
            print("An error occurred:", e)
