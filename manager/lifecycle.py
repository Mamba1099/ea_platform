from __future__ import annotations

from enum import Enum
from threading import Lock

from ipc.file_bridge import EAFileBridge
from ipc.protocol import CommandResult, EACommand
from mt5_runtime import MT5Runtime
from registry import EARegistry


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

    # =========================================================
    # INTERNAL COMMAND HANDLING
    # =========================================================

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

    # =========================================================
    # START
    # =========================================================

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
                pid = self.runtime.start()

                self._send_ea_command(
                    ea_id,
                    EACommand.START,
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

    # =========================================================
    # PAUSE
    # =========================================================

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

    # =========================================================
    # RESUME
    # =========================================================

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

    # =========================================================
    # STOP
    # =========================================================

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

    # =========================================================
    # CLOSE BASKET
    # =========================================================

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

    # =========================================================
    # STATUS
    # =========================================================

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

    # =========================================================
    # HEALTH
    # =========================================================

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
