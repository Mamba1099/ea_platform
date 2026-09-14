from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional
from uuid import uuid4
import time

from .protocol import (
    CommandResult,
    EACommand,
    EACommandAck,
    EACommandMessage,
    EAStatusMessage,
)


class FileBridgeError(RuntimeError):
    """Raised when the IPC file bridge fails."""


class EAFileBridge:
    """
    File-based IPC bridge between the Python manager and MQL5 EAs.

    Directory layout:

        <shared_dir>/
        └── AI_BASKET_EA/
            ├── commands/
            │   └── <request_id>.json
            ├── acks/
            │   └── <request_id>.json
            └── status.json

    The same structure can be used for every EA.
    """

    def __init__(
        self,
        shared_dir: str | Path,
    ) -> None:
        self.shared_dir = Path(shared_dir).expanduser().resolve()

        self._locks: dict[str, Lock] = {}

        self.shared_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _lock_for(self, ea_id: str) -> Lock:
        if ea_id not in self._locks:
            self._locks[ea_id] = Lock()

        return self._locks[ea_id]

    def _ea_dir(self, ea_id: str) -> Path:
        if not ea_id.strip():
            raise ValueError("EA ID cannot be empty.")

        return self.shared_dir / ea_id

    def _commands_dir(self, ea_id: str) -> Path:
        path = self._ea_dir(ea_id) / "commands"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _acks_dir(self, ea_id: str) -> Path:
        path = self._ea_dir(ea_id) / "acks"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _status_file(self, ea_id: str) -> Path:
        self._ea_dir(ea_id).mkdir(
            parents=True,
            exist_ok=True,
        )

        return self._ea_dir(ea_id) / "status.json"

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _write_json_atomic(
        path: Path,
        payload: dict,
    ) -> None:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
        )

        temp_path = Path(temp_name)

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    payload,
                    file,
                    indent=2,
                    sort_keys=True,
                )

                file.flush()
                os.fsync(file.fileno())

            os.replace(
                temp_path,
                path,
            )

        except Exception:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

            raise

    @staticmethod
    def _read_json(path: Path) -> dict:
        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except FileNotFoundError as exc:
            raise FileBridgeError(f"IPC file not found: {path}") from exc

        except json.JSONDecodeError as exc:
            raise FileBridgeError(f"Invalid JSON in IPC file: {path}") from exc

        if not isinstance(data, dict):
            raise FileBridgeError(f"IPC JSON must contain an object: {path}")

        return data

    def send_command(
        self,
        ea_id: str,
        command: EACommand,
        request_id: Optional[str] = None,
    ) -> EACommandMessage:
        """
        Write a command for the EA.

        Every command receives a unique request ID.
        """

        message = EACommandMessage(
            ea_id=ea_id,
            request_id=request_id or str(uuid4()),
            command=command,
            timestamp=self._timestamp(),
        )

        command_path = self._commands_dir(ea_id) / f"{message.request_id}.json"

        with self._lock_for(ea_id):
            self._write_json_atomic(
                command_path,
                message.to_dict(),
            )

        return message

    def wait_for_ack(
        self,
        ea_id: str,
        request_id: str,
        timeout: float = 5.0,
        poll_interval: float = 0.25,
    ) -> EACommandAck:
        """
        Wait for the EA to acknowledge a command.

        Raises:
            FileBridgeError: if the timeout expires.
        """

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            ack = self.read_ack(
                ea_id,
                request_id,
            )

            if ack is not None:
                return ack

            time.sleep(poll_interval)

        command_path = self._commands_dir(ea_id) / f"{request_id}.json"

        try:
            command_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise FileBridgeError(
            f"Timed out waiting for EA ACK: " f"ea_id={ea_id}, request_id={request_id}"
        )

    def read_ack(
        self,
        ea_id: str,
        request_id: str,
    ) -> Optional[EACommandAck]:
        """
        Read the EA acknowledgement for a request.

        Returns None when the EA has not acknowledged it yet.
        """

        path = self._acks_dir(ea_id) / f"{request_id}.json"

        if not path.exists():
            return None

        data = self._read_json(path)

        return EACommandAck.from_dict(data)

    def read_status(
        self,
        ea_id: str,
    ) -> Optional[EAStatusMessage]:
        """
        Read the latest status published by an EA.
        """

        path = self._status_file(ea_id)

        if not path.exists():
            return None

        data = self._read_json(path)

        return EAStatusMessage.from_dict(data)

    def clear_command(
        self,
        ea_id: str,
        request_id: str,
    ) -> None:
        path = self._commands_dir(ea_id) / f"{request_id}.json"

        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def clear_ack(
        self,
        ea_id: str,
        request_id: str,
    ) -> None:
        path = self._acks_dir(ea_id) / f"{request_id}.json"

        try:
            path.unlink()
        except FileNotFoundError:
            pass
