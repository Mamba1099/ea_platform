from __future__ import annotations

from enum import Enum
from threading import Lock
import time
from manager.ipc.file_bridge import EAFileBridge
from manager.ipc.protocol import CommandResult, EACommand
from manager.mt5_runtime import MT5Runtime
from manager.registry import EARegistry


class EAStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


class EALifecycleController:
    """
    Controls the lifecycle of registered EAs.

    Responsibilities:
        - Manage logical EA state in EARegistry.
        - Start and stop the MT5 terminal.
        - Send control commands to the actual EA through EAFileBridge.
        - Wait for and validate EA acknowledgements.
        - Synchronize the registry with EA-published status.

    Important distinction:

        MT5Runtime
            Controls the MetaTrader 5 terminal process.

        EAFileBridge
            Controls communication with an EA already attached to MT5.

        EALifecycleController
            Coordinates the two.
    """

    def __init__(
        self,
        registry: EARegistry,
        runtime: MT5Runtime,
        bridge: EAFileBridge,
    ) -> None:
        self.registry = registry
        self.runtime = runtime
        self.bridge = bridge
        self._lock = Lock()

    def _send_ea_command(
        self,
        ea_id: str,
        command: EACommand,
        timeout: float = 5.0,
    ):
        """
        Send a command to the EA and wait for its acknowledgement.

        The registry is NOT changed here.
        The caller changes registry state only after the EA
        confirms successful execution.
        """

        message = self.bridge.send_command(
            ea_id,
            command,
        )

        ack = self.bridge.wait_for_ack(
            ea_id,
            message.request_id,
            timeout=timeout,
        )

        if ack.result != CommandResult.EXECUTED:
            raise RuntimeError(
                f"EA command failed: "
                f"ea_id={ea_id} "
                f"command={command.value} "
                f"result={ack.result.value} "
                f"message={ack.message}"
            )

        return ack

    def _wait_for_ea_ready(
        self,
        ea_id: str,
        previous_status_mtime: float | None = None,
        timeout: float = 30.0,
        poll_interval: float = 0.5,
    ) -> bool:
        """
        Wait until the EA has published fresh telemetry after
        the MT5 runtime has been started.
        """

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            try:
                status_path = self.bridge._status_file(ea_id)

                if not status_path.exists():
                    time.sleep(poll_interval)
                    continue

                current_mtime = status_path.stat().st_mtime

                if (
                    previous_status_mtime is not None
                    and current_mtime <= previous_status_mtime
                ):
                    time.sleep(poll_interval)
                    continue

                status = self.bridge.read_status(ea_id)

                if status is not None and status.terminal_connected:
                    return True

            except OSError:
                pass

            time.sleep(poll_interval)

        return False

    def start(self, ea_id: str):
        """
        Start the MT5 terminal and enable the EA.

        Sequence:

            STOPPED
                ↓
            STARTING
                ↓
            MT5 running
                ↓
            EA telemetry ready
                ↓
            EA START command
                ↓
            EA ACK
                ↓
            RUNNING
        """

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
                previous_status_mtime = None

                try:
                    status_path = self.bridge._status_file(ea_id)
                    if status_path.exists():
                        previous_status_mtime = status_path.stat().st_mtime
                except OSError:
                    previous_status_mtime = None

                pid = self.runtime.start()
                if not self._wait_for_ea_ready(
                    ea_id,
                    previous_status_mtime=previous_status_mtime,
                    timeout=30.0,
                    poll_interval=0.5,
                ):
                    raise RuntimeError(
                        f"EA {ea_id} did not become ready " f"after MT5 startup."
                    )

                self._send_ea_command(
                    ea_id,
                    EACommand.START,
                    timeout=15.0,
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

                print(f"EA started successfully. " f"MT5 PID={pid}")

                return self.registry.get(ea_id)

            except Exception as exc:
                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.ERROR.value,
                )

                raise RuntimeError(f"Failed to start EA {ea_id}: {exc}") from exc

    def pause(self, ea_id: str):
        """
        Pause EA trading without shutting down MT5.

        Existing basket management remains inside the EA.
        """

        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status != EAStatus.RUNNING.value:
                return ea

            self._send_ea_command(
                ea_id,
                EACommand.PAUSE,
            )

            self.registry.set_enabled(
                ea_id,
                False,
            )

            self.registry.set_status(
                ea_id,
                EAStatus.PAUSED.value,
            )

            self.registry.heartbeat(ea_id)

            return self.registry.get(ea_id)

    def resume(self, ea_id: str):
        """
        Resume EA trading.

        MT5 must still be running.
        """

        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status != EAStatus.PAUSED.value:
                return ea

            if not self.runtime.is_running():
                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.STOPPED.value,
                )

                raise RuntimeError("Cannot resume EA because " "MT5 is not running.")

            self._send_ea_command(
                ea_id,
                EACommand.RESUME,
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
        """
        Stop the EA and shut down the MT5 terminal.

        Sequence:

            RUNNING/PAUSED
                ↓
            STOPPING
                ↓
            EA STOP
                ↓
            MT5 STOP
                ↓
            STOPPED
        """

        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status == EAStatus.STOPPED.value:
                return ea

            self.registry.set_status(
                ea_id,
                EAStatus.STOPPING.value,
            )

            try:
                if self.runtime.is_running():
                    self._send_ea_command(
                        ea_id,
                        EACommand.STOP,
                    )

                stopped = self.runtime.stop()

                if not stopped:
                    raise RuntimeError("MT5 process did not stop cleanly.")

                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.STOPPED.value,
                )

                self.registry.heartbeat(ea_id)

                return self.registry.get(ea_id)

            except Exception as exc:
                self.registry.set_status(
                    ea_id,
                    EAStatus.ERROR.value,
                )

                raise RuntimeError(f"Failed to stop EA {ea_id}: {exc}") from exc

    def restart_runtime_for_deployment(self, ea_id):
        """
        Stop the entire MT5 runtime for a deployment restart.

        Unlike the normal stop() operation, deployment does not send
        an EA STOP command first. The MT5 process itself is being
        restarted, so sending an EA command immediately before killing
        the terminal can leave an orphaned IPC command.
        """
        with self._lock:
            ea = self.registry.get(ea_id)

            if ea is None:
                raise RuntimeError(f"Unknown EA: {ea_id}")

            self.registry.set_status(
                ea_id,
                EAStatus.STOPPING.value,
            )

            try:
                if self.runtime.is_running():
                    stopped = self.runtime.stop()

                    if not stopped:
                        raise RuntimeError("MT5 process did not stop cleanly.")

                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.STOPPED.value,
                )

                return True

            except Exception as exc:
                self.registry.set_enabled(
                    ea_id,
                    False,
                )

                self.registry.set_status(
                    ea_id,
                    EAStatus.ERROR.value,
                )

                raise RuntimeError(f"Failed to stop MT5 for deployment: {exc}") from exc

    def close_basket(self, ea_id: str):
        """
        Request that the EA close its current basket.

        This does NOT change the lifecycle state.

        Example:

            RUNNING + CLOSE_BASKET
                ↓
            basket closes
                ↓
            EA remains RUNNING
        """

        with self._lock:
            ea = self.registry.get(ea_id)

            if ea.status not in (
                EAStatus.RUNNING.value,
                EAStatus.PAUSED.value,
            ):
                raise RuntimeError(
                    f"Cannot close basket while EA " f"is in state {ea.status}."
                )

            return self._send_ea_command(
                ea_id,
                EACommand.CLOSE_BASKET,
            )

    def status(self, ea_id: str):
        """
        Return the locally cached registry state.
        """

        return self.registry.get(ea_id)

    def refresh_status(self, ea_id: str):
        """
        Synchronize the local registry with the latest
        status published by the actual EA.
        """

        status = self.bridge.read_status(ea_id)

        if status is None:
            return self.registry.get(ea_id)

        self.registry.set_status(
            ea_id,
            status.status.value,
        )

        self.registry.set_enabled(
            ea_id,
            status.enabled,
        )

        return self.registry.get(ea_id)

    def health(self, ea_id: str) -> dict:
        """
        Return combined MT5 + EA health information.
        """

        ea = self.registry.get(ea_id)

        runtime = self.runtime.heartbeat()
        status = self.bridge.read_status(ea_id)

        return {
            "ea_id": ea.ea_id,
            "registry_status": ea.status,
            "registry_enabled": ea.enabled,
            "mt5": runtime,
            "ea_status": (status.to_dict() if status is not None else None),
        }
