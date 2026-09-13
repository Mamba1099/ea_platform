from __future__ import annotations

from enum import Enum
from threading import Lock

from registry import EARegistry


class EAStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"


class EALifecycleController:
    """
    Controls the logical lifecycle of registered EAs.

    At this stage, lifecycle.py manages EA state only.
    Actual MT5 process control will be connected later
    through mt5_runtime.py.
    """

    def __init__(self, registry: EARegistry) -> None:
        self.registry = registry
        self._lock = Lock()

    def start(self, ea_id: str):
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status in (
                EAStatus.RUNNING,
                EAStatus.STARTING,
            ):
                return ea

            self.registry.set_status(
                ea_id,
                EAStatus.STARTING.value,
            )

            # MT5 process control will be connected later.
            self.registry.set_enabled(
                ea_id,
                True,
            )

            self.registry.set_status(
                ea_id,
                EAStatus.RUNNING.value,
            )

            return self.registry.get(ea_id)

    def pause(self, ea_id: str):
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status != EAStatus.RUNNING:
                return ea

            self.registry.set_enabled(
                ea_id,
                False,
            )

            self.registry.set_status(
                ea_id,
                EAStatus.PAUSED.value,
            )

            return self.registry.get(ea_id)

    def resume(self, ea_id: str):
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status != EAStatus.PAUSED:
                return ea

            self.registry.set_enabled(
                ea_id,
                True,
            )

            self.registry.set_status(
                ea_id,
                EAStatus.RUNNING.value,
            )

            return self.registry.get(ea_id)

    def stop(self, ea_id: str):
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status == EAStatus.STOPPED:
                return ea

            self.registry.set_status(
                ea_id,
                EAStatus.STOPPING.value,
            )

            # MT5 process shutdown will be connected later.
            self.registry.set_enabled(
                ea_id,
                False,
            )

            self.registry.set_status(
                ea_id,
                EAStatus.STOPPED.value,
            )

            return self.registry.get(ea_id)

    def status(self, ea_id: str):
        return self.registry.get(ea_id)