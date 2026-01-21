import json
import os
import threading
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

        line = json.dumps(event, ensure_ascii=False)
        with self._lock:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(line + "\n")
