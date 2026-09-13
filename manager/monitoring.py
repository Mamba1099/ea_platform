from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Optional

from manager.ipc.file_bridge import EAFileBridge
from manager.registry import EARegistry


@dataclass
class EAHealth:
    """
    Runtime health information for one EA.

    file_age_seconds is based on the Linux filesystem modification
    time of status.json, not the timestamp written by the EA.

    This is important because MT5 TimeCurrent() can remain unchanged
    while the market/server is closed.
    """

    ea_id: str
    status: str
    enabled: bool

    status_available: bool
    file_age_seconds: Optional[float]

    healthy: bool
    stale: bool
    terminal_connected: bool

    message: str = ""


class EAMonitor:
    """
    Synchronizes EA telemetry from the IPC bridge into the registry
    and evaluates EA health.

    Responsibilities:
        - Read status.json.
        - Update registry status/enabled state.
        - Measure status-file freshness.
        - Detect stale/offline EA telemetry.
        - Provide a health snapshot.

    This class does NOT:
        - start or stop MT5,
        - send trading commands,
        - modify EA strategy state.
    """

    def __init__(
        self,
        registry: EARegistry,
        bridge: EAFileBridge,
        stale_after_seconds: float = 10.0,
    ) -> None:
        if stale_after_seconds <= 0:
            raise ValueError("stale_after_seconds must be greater than zero.")

        self.registry = registry
        self.bridge = bridge
        self.stale_after_seconds = stale_after_seconds

        self._health: dict[str, EAHealth] = {}
        self._lock = Lock()

    # =========================================================
    # INTERNAL
    # =========================================================

    def _status_file(
        self,
        ea_id: str,
    ) -> Path:
        """
        Resolve the local status.json path used by the file bridge.
        """

        return self.bridge.shared_dir / ea_id / "status.json"

    def _file_age_seconds(
        self,
        path: Path,
    ) -> Optional[float]:
        if not path.exists():
            return None

        try:
            modified = path.stat().st_mtime
        except OSError:
            return None

        return max(
            0.0,
            time.time() - modified,
        )

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh(
        self,
        ea_id: str,
    ) -> EAHealth:
        """
        Read the EA's latest status and synchronize the registry.

        Returns:
            EAHealth describing the current EA health.
        """

        with self._lock:
            status = self.bridge.read_status(ea_id)

            status_file = self._status_file(ea_id)
            age = self._file_age_seconds(status_file)

            if status is None:
                health = EAHealth(
                    ea_id=ea_id,
                    status="OFFLINE",
                    enabled=False,
                    status_available=False,
                    file_age_seconds=age,
                    healthy=False,
                    stale=True,
                    terminal_connected=False,
                    message="No valid EA status available.",
                )

                self._health[ea_id] = health

                return health

            # Synchronize registry with actual EA state.
            self.registry.set_status(
                ea_id,
                status.status.value,
            )

            self.registry.set_enabled(
                ea_id,
                status.enabled,
            )

            # File modification time is our real heartbeat signal.
            stale = age is None or age > self.stale_after_seconds

            healthy = not stale and status.terminal_connected

            if stale:
                message = (
                    f"Status file is stale " f"(age={age:.1f}s)."
                    if age is not None
                    else "Status file timestamp unavailable."
                )
            elif not status.terminal_connected:
                message = "EA reports terminal disconnected."
            else:
                message = "EA telemetry healthy."

            health = EAHealth(
                ea_id=ea_id,
                status=status.status.value,
                enabled=status.enabled,
                status_available=True,
                file_age_seconds=age,
                healthy=healthy,
                stale=stale,
                terminal_connected=status.terminal_connected,
                message=message,
            )

            self._health[ea_id] = health

            return health

    # =========================================================
    # REFRESH ALL
    # =========================================================

    def refresh_all(self) -> dict[str, EAHealth]:
        """
        Refresh every registered EA.
        """

        results: dict[str, EAHealth] = {}

        for ea in self.registry.list_all():
            results[ea.ea_id] = self.refresh(ea.ea_id)

        return results

    # =========================================================
    # HEALTH
    # =========================================================

    def health(
        self,
        ea_id: str,
    ) -> Optional[EAHealth]:
        """
        Return the most recently calculated health state.
        """

        with self._lock:
            return self._health.get(ea_id)

    def health_dict(
        self,
        ea_id: str,
    ) -> Optional[dict]:
        """
        Return health as an API-friendly dictionary.
        """

        health = self.health(ea_id)

        if health is None:
            return None

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

    def health_all(self) -> dict[str, dict]:
        """
        Return health information for all registered EAs.
        """

        with self._lock:
            return {
                ea_id: {
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
                for ea_id, health in self._health.items()
            }
