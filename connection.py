from logging import Logger
from threading import Event, Thread

from obdii import Connection
from obdii.errors import ResponseBaseError

from config import DEFAULT_COMMANDS
from polling import PollingManager
from storage import StorageUpdater


class ConnectionManager:
    def __init__(self, connection: Connection, storage_updater: StorageUpdater, logger: Logger):
        self.connection = connection
        self.storage_updater = storage_updater
        self.logger = logger

        self._running = False
        self._is_startup = True

        self.polling_stop = Event()
        self.polling_error = Event()

        self.fetch_thread = None

        self.polling_manager = PollingManager()
        for key, value in DEFAULT_COMMANDS.items():
            self.polling_manager.register(key, value)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self.fetch_thread = Thread(target=self.background_fetch, daemon=True)
        self.fetch_thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self.polling_stop.set()
        if self.fetch_thread and self.fetch_thread.is_alive():
            self.fetch_thread.join()
        self.fetch_thread = None

    def ensure_polling(self) -> None:
        if not self.fetch_thread or not self.fetch_thread.is_alive() or self.polling_error.is_set():
            self.reconnect()

    def reconnect(self) -> None:
        if not self._is_startup:
            self.logger.warning("Attempting to reconnect")
        
        self.stop()
        self.connection.close()

        try:
            self.connection.connect()
            self._is_startup = False
        except ConnectionError:
            self.logger.warning("Connection failed")
            return
        
        self.polling_stop.clear()
        self.polling_error.clear()
        self.start()

    def background_fetch(self) -> None:
        # _cache = {}
        while self._running and not self.polling_stop.is_set():
            to_fetch = self.polling_manager.get_cycle()
            for command in to_fetch:
                try:
                    response = self.connection.query(command)
                    value = response.value
                    if value:
                        # _cache[command] = value
                        self.storage_updater.update_single(command, value)
                    else:
                        self.logger.warning(f"No data for command: {command}; value: {value}")

                except KeyError:
                    self.logger.warning(f"Unknown command: {command}")

                except ResponseBaseError as e:
                    self.logger.warning(f"ResponseError {str(e)}")
                except Exception as e:
                    self.logger.critical(f"CriticalError {str(e)}")
                    self.storage_updater.clear_all()

                    self.polling_error.set()
                    self.polling_stop.set()
                    return