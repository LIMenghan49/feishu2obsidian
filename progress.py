import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PROGRESS_FILE = "progress.json"


class Progress:
    """断点续传：记录已完成/失败的节点，中断后可从上次位置继续。"""

    def __init__(self, path: str = PROGRESS_FILE):
        self.path = path
        self._data = {"last_run": None, "completed": {}, "failed": {}}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info("加载进度文件: %d 已完成, %d 失败",
                        len(self._data["completed"]), len(self._data["failed"]))

    def _save(self):
        self._data["last_run"] = datetime.now().isoformat()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def is_done(self, obj_token: str) -> bool:
        return obj_token in self._data["completed"]

    def mark_done(self, obj_token: str, title: str, path: str):
        self._data["completed"][obj_token] = {"title": title, "path": path}
        # 如果之前在 failed 列表里，移除
        self._data["failed"].pop(obj_token, None)
        self._save()

    def mark_failed(self, obj_token: str, title: str, error: str):
        entry = self._data["failed"].get(obj_token, {"title": title, "retries": 0})
        entry["error"] = error
        entry["retries"] = entry.get("retries", 0) + 1
        self._data["failed"][obj_token] = entry
        self._save()

    @property
    def completed(self) -> dict:
        return self._data["completed"]

    @property
    def failed(self) -> dict:
        return self._data["failed"]

    def summary(self) -> str:
        return (f"进度: {len(self._data['completed'])} 完成, "
                f"{len(self._data['failed'])} 失败")
