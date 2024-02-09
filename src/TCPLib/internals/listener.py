import logging
import threading

from client_processor import ClientProcessor
logging.getLogger(__name__)


class Listener:
    def __init__(self, host, port, server_obj):
        self._addr = (host, port)
        self._soc = None
        self._server_obj = server_obj

    @staticmethod
    def _generate_client_id():
        pass

    def _accept_connection(self):
        pass

    def addr(self):
        return self._addr

    def mainloop(self):
        while self._server_obj.is_running():
            logging.debug("SERVER: Listening for new connections...")
            try:
                self._soc.listen()
                client_soc, client_addr = self._soc.accept()
                if self._server_obj.is_full():
                    client_soc.close()
                    continue
                processor = ClientProcessor(self._generate_client_id(), self, client_addr[0], client_addr[1],
                                            client_soc)
                self._server_obj.update_connected_clients(processor)
                proc_th = threading.Thread(target=processor.process_client)
                proc_th.start()
                logging.info(f"SERVER: Client at {processor.addr()[0]} @ {processor.addr()[1]} was connected")
            except OSError as e:
                logging.debug("Exception", exc_info=e)
                logging.info("Server shutdown")
                break
        logging.info("Server shutdown")

