from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime
from uuid import uuid4


def _default_now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ImportTaskStore:
    def __init__(self, *, log_limit: int = 300, now_text: Callable[[], str] = _default_now_text):
        self.log_limit = log_limit
        self.now_text = now_text
        self._tasks = {}
        self._lock = threading.Lock()

    def create(self, username: str, account_id: int | None, filename: str) -> str:
        task_id = uuid4().hex
        task = {
            "id": task_id,
            "filename": filename,
            "status": "queued",
            "message": "تم إنشاء مهمة الاستيراد وبانتظار بدء المعالجة.",
            "created_at": self.now_text(),
            "started_at": "",
            "finished_at": "",
            "total": 0,
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "error_count": 0,
            "percent": 0,
            "current_step": "بانتظار البدء",
            "logs": [],
            "errors": [],
            "username": username or "",
            "account_id": account_id,
        }
        with self._lock:
            self._tasks[task_id] = task
        return task_id

    def get(self, task_id: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            return {**task, "logs": list(task.get("logs", [])), "errors": list(task.get("errors", []))}

    def update(self, task_id: str, **kwargs) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.update(kwargs)
            total = int(task.get("total") or 0)
            processed = int(task.get("processed") or 0)
            task["percent"] = min(100, round((processed / total) * 100)) if total else 0

    def append_log(self, task_id: str, message: str, *, is_error: bool = False) -> None:
        timestamped = f"[{self.now_text()}] {message}"
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.setdefault("logs", []).append(timestamped)
            if len(task["logs"]) > self.log_limit:
                task["logs"] = task["logs"][-self.log_limit :]
            if is_error:
                task.setdefault("errors", []).append(timestamped)
                task["error_count"] = len(task["errors"])

    def finalize(self, task_id: str, status: str, message: str) -> None:
        self.update(task_id, status=status, message=message, finished_at=self.now_text(), current_step=message)


_store = ImportTaskStore()


def configure_import_task_store(*, now_text: Callable[[], str] | None = None, log_limit: int | None = None) -> None:
    if now_text is not None:
        _store.now_text = now_text
    if log_limit is not None:
        _store.log_limit = log_limit


def create_import_task(username: str, account_id: int | None, filename: str) -> str:
    return _store.create(username, account_id, filename)


def get_import_task(task_id: str):
    return _store.get(task_id)


def update_import_task(task_id: str, **kwargs) -> None:
    _store.update(task_id, **kwargs)


def append_import_log(task_id: str, message: str, is_error: bool = False) -> None:
    _store.append_log(task_id, message, is_error=is_error)


def finalize_import_task(task_id: str, status: str, message: str) -> None:
    _store.finalize(task_id, status, message)
