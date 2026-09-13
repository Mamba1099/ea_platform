from __future__ import annotations

from enum import Enum
from threading import Lock

from mt5_runtime import MT5Runtime
from registry import EARegistry


class EAStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"


class EALifecycleController:
    """
    Controls the lifecycle of a registered EA.

    This controller manages both:
    1. Logical EA state in the registry.
    2. The MT5 runtime process.

    EA-specific trading commands are not handled here.
    """

    def __init__(
        self,
        registry: EARegistry,
        runtime: MT5Runtime,
    ) -> None:
        self.registry = registry
        self.runtime = runtime
        self._lock = Lock()

    def start(self, ea_id: str):
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status in (
                EAStatus.RUNNING.value,
                EAStatus.STARTING.value,
            ):
                return ea

            self.registry.set_status(
                ea_id,
                EAStatus.STARTING.value,
            )

            try:
                pid = self.runtime.start()
                self.registry.set_enabled(
                    ea_id,
                    True,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.RUNNING.value,
                )

                self.registry.heartbeat(ea_id)

                print(
                    f"MT5 started successfully. PID={pid}"
                )

                return self.registry.get(ea_id)

            except Exception as exc:
                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.STOPPED.value,
                )

                raise RuntimeError(
                    f"Failed to start EA {ea_id}: {exc}"
                ) from exc

    def pause(self, ea_id: str):
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status != EAStatus.RUNNING.value:
                return ea

            # For now pause only disables the EA logically.
            # The MT5 terminal remains running.
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

            if ea.status != EAStatus.PAUSED.value:
                return ea

            if not self.runtime.is_running():
                self.registry.set_status(
                    ea_id,
                    EAStatus.STOPPED.value,
                )

                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                raise RuntimeError(
                    "Cannot resume EA because MT5 is not running."
                )

            self.registry.set_enabled(
                ea_id,
                True,
            )

            self.registry.set_status(
                ea_id,
                EAStatus.RUNNING.value,
            )

            self.registry.heartbeat(ea_id)

            return self.registry.get(ea_id)

    def stop(self, ea_id: str):
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status == EAStatus.STOPPED.value:
                return ea

            self.registry.set_status(
                ea_id,
                EAStatus.STOPPING.value,
            )

            try:
                self.runtime.stop()

                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.STOPPED.value,
                )

                return self.registry.get(ea_id)

            except Exception as exc:
                raise RuntimeError(
                    f"Failed to stop EA {ea_id}: {exc}"
                ) from exc

    def status(self, ea_id: str):
        return self.registry.get(ea_id)