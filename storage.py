from typing import Any, Dict

from threading import Lock

class StorageUpdater():
    def __init__(self, storage: Dict[str, Any]):
        self.storage_lock = Lock()
        self.storage = storage

    def update_storage(self, cp_storage: Dict[str, Any]) -> None:
        with self.storage_lock:
            keys_to_remove = set(cp_storage.keys()) - set(self.storage.keys())
            for key in keys_to_remove:
                cp_storage.pop(key)
            self.storage.update(cp_storage)
    
    def update_single(self, key: str, value: Any) -> None:
        with self.storage_lock:
            self.storage[key] = value
    
    def copy(self) -> Dict[str, Any]:
        with self.storage_lock:
            return self.storage.copy()
    
    def clear_all(self, value: Any = None) -> None:
        with self.storage_lock:
            for key in self.storage.keys():
                self.storage[key] = value