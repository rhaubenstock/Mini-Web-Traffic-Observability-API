import json
import os
import threading
import fcntl
from datetime import datetime, timezone
from typing import Any, Dict

class JsonlLogger:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("")

    def log(self, event: Dict[str, Any]) -> None:
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()

        line = (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")

        # Open in binary append so we control exactly what gets written.
        with open(self.filepath, "ab") as f:
            # EXCLUSIVE lock: only one process can hold it at a time.
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(line)
                f.flush()
                # Optional: guarantees it hits disk (slower)
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
