from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from manager.registry import EARegistry
from manager.ipc.file_bridge import EAFileBridge
from manager.mt5_runtime import MT5Runtime


@dataclass
class EAHealth:
    ea_id: str
    status: str
    enabled: bool
    status_available: bool
    file_age_seconds: Optional[float]
    healthy: bool
    stale: bool
    terminal_connected: bool
    message: str


class EAMonitor:
    def __init__(
        self,
        registry: EARegistry,
        bridge: EAFileBridge,
        runtime: MT5Runtime,
        stale_threshold: float = 10.0,
    ):
        self.registry = registry
        self.bridge = bridge
        self.runtime = runtime
        self.stale_threshold = stale_threshold

    def refresh(self, ea_id: str) -> EAHealth:
        instance = self.registry.get(ea_id)

        if instance is None:
            raise ValueError(f"Unknown EA: {ea_id}")

        status_message = self.bridge.read_status(ea_id)

        if status_message is None:
            self.registry.set_status(ea_id, "ERROR")
            return EAHealth(
                ea_id=ea_id,
                status="ERROR",
                enabled=False,
                status_available=False,
                file_age_seconds=None,
                healthy=False,
                stale=True,
                terminal_connected=self.runtime.is_running(),
                message="EA status telemetry is unavailable.",
            )

        status_path = self.bridge._status_file(ea_id)

        file_age_seconds: Optional[float] = None

        try:
            modified = status_path.stat().st_mtime
            file_age_seconds = max(0.0, time.time() - modified)
        except OSError:
            file_age_seconds = None

        stale = file_age_seconds is None or file_age_seconds > self.stale_threshold

        terminal_connected = bool(status_message.terminal_connected)
        healthy = not stale and terminal_connected

        status = status_message.status
        enabled = status_message.enabled

        # The EA itself is authoritative when fresh.
        if healthy:
            self.registry.set_status(ea_id, status)
            self.registry.set_enabled(ea_id, enabled)

            self.registry.heartbeat(ea_id)

            message = "EA telemetry healthy."

        else:
            self.registry.set_status(ea_id, "ERROR")
            self.registry.set_enabled(ea_id, False)

            message = (
                "EA telemetry is stale."
                if stale
                else "EA terminal connection is unavailable."
            )

        return EAHealth(
            ea_id=ea_id,
            status=status if healthy else "ERROR",
            enabled=enabled if healthy else False,
            status_available=True,
            file_age_seconds=file_age_seconds,
            healthy=healthy,
            stale=stale,
            terminal_connected=terminal_connected,
            message=message,
        )

    def refresh_all(self) -> list[EAHealth]:
        results: list[EAHealth] = []

        for instance in self.registry.list_all():
            try:
                results.append(self.refresh(instance.ea_id))
            except Exception as exc:
                self.registry.set_status(instance.ea_id, "ERROR")
                self.registry.set_enabled(instance.ea_id, False)

                results.append(
                    EAHealth(
                        ea_id=instance.ea_id,
                        status="ERROR",
                        enabled=False,
                        status_available=False,
                        file_age_seconds=None,
                        healthy=False,
                        stale=True,
                        terminal_connected=self.runtime.is_running(),
                        message=f"Monitoring error: {exc}",
                    )
                )

        return results

    def health(self, ea_id: str) -> EAHealth:
        return self.refresh(ea_id)

    def health_dict(self, ea_id: str) -> dict:
        health = self.health(ea_id)
        return {
            "ea_id": health.ea_id,
            "status": health.status,
            "enabled": health.enabled,
            "status_available": health.status_available,
            "file_age_seconds": health.file_age_seconds,
            "healthy": health.healthy,
            "stale": health.stale,
            "terminal_connected": health.terminal_connected,
            "message": health.message,
        }

    def health_all(self) -> list[dict]:
        return [
            {
                "ea_id": item.ea_id,
                "status": item.status,
                "enabled": item.enabled,
                "status_available": item.status_available,
                "file_age_seconds": item.file_age_seconds,
                "healthy": item.healthy,
                "stale": item.stale,
                "terminal_connected": item.terminal_connected,
                "message": item.message,
            }
            for item in self.refresh_all()
        ]


class EAMonitorWatchdog:
    """
    Background monitor for all registered EAs.

    The watchdog deliberately only observes and synchronizes state.
    It does not automatically restart or trade on behalf of an EA.
    """

    def __init__(
        self,
        monitor: EAMonitor,
        event_store,
        instance_store,
        interval_seconds: float = 2.0,
    ):
        self.monitor = monitor
        self.event_store = event_store
        self.instance_store = instance_store
        self.interval_seconds = interval_seconds

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = False

        self._previous_states: dict[str, tuple[str, bool, bool]] = {}

    def start(self) -> None:
        if self._started:
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="ea-monitor-watchdog",
            daemon=True,
        )

        self._thread.start()
        self._started = True

        print(f"[watchdog] started " f"(interval={self.interval_seconds:.1f}s)")

    def stop(self) -> None:
        if not self._started:
            return

        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=5.0)

        self._thread = None
        self._started = False

        print("[watchdog] stopped")

    def is_running(self) -> bool:
        return self._started and self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                results = self.monitor.refresh_all()

                for result in results:
                    previous = self._previous_states.get(result.ea_id)

                    current = (
                        result.status,
                        result.healthy,
                        result.stale,
                    )

                    if previous is not None:
                        self._detect_transition(
                            previous,
                            current,
                            result,
                        )

                    self._previous_states[result.ea_id] = current

                    if previous is None:
                        self._persist_state(result)

                    if result.healthy:
                        print(
                            f"[watchdog] {result.ea_id}: "
                            f"{result.status.value if hasattr(result.status, 'value') else result.status} "
                            f"age={result.file_age_seconds:.2f}s"
                        )
                    else:
                        print(
                            f"[watchdog] {result.ea_id}: "
                            f"UNHEALTHY - {result.message}"
                        )

            except Exception as exc:
                print(f"[watchdog] cycle failed: {exc}")

            self._stop_event.wait(self.interval_seconds)

    @staticmethod
    def _status_event_type(
        previous_status: str,
        current_status: str,
    ) -> str:
        mapping = {
            "PAUSED": "EA_PAUSED",
            "RUNNING": "EA_RESUMED",
            "STOPPED": "EA_STOPPED",
            "ERROR": "EA_ERROR",
            "STARTING": "EA_STARTING",
            "STOPPING": "EA_STOPPING",
        }

        return mapping.get(
            current_status,
            "EA_STATUS_CHANGED",
        )

    def _persist_state(self, result: EAHealth) -> None:
        self.instance_store.persist_status(
            ea_id=result.ea_id,
            status=(
                result.status.value
                if hasattr(result.status, "value")
                else result.status
            ),
            enabled=result.enabled,
        )

    def _detect_transition(
        self,
        previous: tuple[str, bool, bool],
        current: tuple[str, bool, bool],
        result: EAHealth,
    ) -> None:
        previous_status, previous_healthy, previous_stale = previous
        current_status, current_healthy, current_stale = current

        previous_status_text = (
            previous_status.value
            if hasattr(previous_status, "value")
            else previous_status
        )

        current_status_text = (
            current_status.value if hasattr(current_status, "value") else current_status
        )

        if previous_stale is False and current_stale is True:
            self.event_store.record(
                result.ea_id,
                "EA_STALE",
                previous_status_text,
                current_status_text,
                result.message,
            )

            self._persist_state(result)
            return

        if previous_healthy is False and current_healthy is True:
            self.event_store.record(
                result.ea_id,
                "EA_RECOVERED",
                previous_status_text,
                current_status_text,
                "EA telemetry recovered.",
            )

            self._persist_state(result)
            return

        if previous_healthy is True and current_healthy is False:
            self.event_store.record(
                result.ea_id,
                "EA_UNHEALTHY",
                previous_status_text,
                current_status_text,
                result.message,
            )

            self._persist_state(result)
            return

        if previous_status != current_status:
            event_type = self._status_event_type(
                previous_status_text,
                current_status_text,
            )

            self.event_store.record(
                result.ea_id,
                event_type,
                previous_status_text,
                current_status_text,
                (
                    f"EA status changed from "
                    f"{previous_status_text} to "
                    f"{current_status_text}."
                ),
            )

            self._persist_state(result)
