from logging import Logger
from threading import Event, Thread
from time import monotonic
from typing import Dict

from obdii import Command, Connection
from obdii.errors import ResponseBaseError

from polling import PollingManager
from storage import StorageUpdater


class ConnectionManager:
    RECONNECT_DELAY = 5.0

    def __init__(self, connection: Connection, storage_updater: StorageUpdater, logger: Logger, default_commands: Dict[Command, int]) -> None:
        self.connection = connection
        self.storage_updater = storage_updater
        self.logger = logger

        self._running = False
        self._is_startup = True
        self._last_reconnect_attempt = 0.0

        self.polling_stop = Event()
        self.polling_error = Event()

        self.fetch_thread = None

        self.polling_manager = PollingManager()
        for key, value in default_commands.items():
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
            now = monotonic()
            if now - self._last_reconnect_attempt < self.RECONNECT_DELAY:
                return
            self._last_reconnect_attempt = now
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
        while self._running and not self.polling_stop.is_set():
            to_fetch = self.polling_manager.get_cycle()
            for command in to_fetch:
                try:
                    response = self.connection.query(command)
                    value = response.value
                    if value is not None:
                        self.storage_updater.update_single(command, value)
                    else:
                        self.logger.warning(f"No data for command: {command}; value: {value}")

                except KeyError:
                    self.logger.warning(f"Unknown command: {command}")

                except ResponseBaseError as e:
                    self.logger.warning(f"ResponseError {e!s}")
                except Exception as e:
                    self.logger.critical(f"CriticalError {e!s}")
                    self.storage_updater.clear_all()

                    self.polling_error.set()
                    self.polling_stop.set()
                    return