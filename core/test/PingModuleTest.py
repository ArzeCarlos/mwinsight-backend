from checkers.ping import Ping
from queue import Queue

class testPing(object):
    @staticmethod
    def testPingModule(host: str='localhost',counter:int=3,timeout: float=1
                       ,packetsize:int=32,itemid:int=1)->None:
        print("Starting application...")
        data_queue = Queue()
        data = {
            'host': host,   
            'pingcount': counter,
            'timeout': timeout,
            'packsize': packetsize,
            'itemid': itemid
        }
        try:
            Ping.get_data(data, data_queue)
            print("Data retrieved from queue:", data_queue.get())
        except Exception as e:
            print("An error occurred:", e)
