from typing import Any, Dict

from threading import Event, Lock

from obdii import Connection, commands


class StorageUpdater():
    def __init__(self, storage: Dict[str, Any], storage_lock: Lock):
        self.storage_lock = storage_lock
        self.storage = storage

    def update_storage(self, cp_storage: Dict[str, Any]) -> None:
        with self.storage_lock:
            keys_to_remove = set(cp_storage.keys()) - set(self.storage.keys())
            for key in keys_to_remove:
                cp_storage.pop(key)
            self.storage.update(cp_storage)


def background_fetch(obd: Connection, storage: Dict[str, Any], storage_lock: Lock, polling_event: Event, polling_error: Event) -> None:
    updater = StorageUpdater(storage, storage_lock)
    stop = polling_event.is_set

    while not stop():
        updates = dict()

        for command_name in tuple(storage.keys()):
            try:
                response = obd.query(commands[command_name])
                updates[command_name] = response.value
            except KeyError:
                updates[command_name] = f"Error: {command_name} not found"
            except Exception as e:
                polling_error.set()
                updates[command_name] = f"CRITError: {str(e)}"

        updater.update_storage(updates)