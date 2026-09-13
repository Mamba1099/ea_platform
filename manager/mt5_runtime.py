from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path
from threading import Lock
from typing import Optional


class MT5RuntimeError(RuntimeError):
    """Raised when the MT5 runtime cannot be started or controlled."""


class MT5Runtime:
    """
    Linux/Wine runtime adapter for MetaTrader 5.

    This class is responsible only for the MT5 terminal process.
    EA lifecycle/state decisions remain in lifecycle.py.
    """

    def __init__(
        self,
        terminal_path: str,
        wine_binary: str = "wine",
        wine_prefix: Optional[str] = None,
        startup_timeout: float = 15.0,
    ) -> None:
        self.terminal_path = Path(terminal_path).expanduser()
        self.wine_binary = wine_binary
        self.wine_prefix = (
            Path(wine_prefix).expanduser()
            if wine_prefix
            else None
        )
        self.startup_timeout = startup_timeout

        self._process: Optional[subprocess.Popen] = None
        self._lock = Lock()

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------

    def _validate_terminal(self) -> None:
        if not self.terminal_path.exists():
            raise MT5RuntimeError(
                f"MT5 terminal not found: {self.terminal_path}"
            )

        if not self.terminal_path.is_file():
            raise MT5RuntimeError(
                f"MT5 terminal path is not a file: {self.terminal_path}"
            )

    def _build_environment(self) -> dict[str, str]:
        env = os.environ.copy()

        if self.wine_prefix is not None:
            env["WINEPREFIX"] = str(self.wine_prefix)

        return env

    # ---------------------------------------------------------
    # PROCESS CONTROL
    # ---------------------------------------------------------

    def start(self) -> int:
        """
        Start MT5 under Wine.

        Returns:
            PID of the Wine launcher process.
        """
        with self._lock:
            if self.is_running():
                return self.pid()

            self._validate_terminal()

            command = [
                self.wine_binary,
                str(self.terminal_path),
            ]

            try:
                self._process = subprocess.Popen(
                    command,
                    cwd=str(self.terminal_path.parent),
                    env=self._build_environment(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except OSError as exc:
                self._process = None
                raise MT5RuntimeError(
                    f"Failed to launch MT5: {exc}"
                ) from exc

            deadline = time.monotonic() + self.startup_timeout

            while time.monotonic() < deadline:
                if self._process.poll() is not None:
                    return_code = self._process.returncode
                    self._process = None

                    raise MT5RuntimeError(
                        f"MT5 exited during startup with code "
                        f"{return_code}"
                    )

                time.sleep(0.25)

            return self._process.pid

    def stop(self, timeout: float = 10.0) -> bool:
        """
        Stop the MT5 process started by this runtime.

        Returns:
            True if stopped successfully.
        """
        with self._lock:
            if self._process is None:
                return True

            process = self._process

            if process.poll() is not None:
                self._process = None
                return True

            try:
                # Because start_new_session=True was used,
                # terminate the complete process group.
                os.killpg(
                    os.getpgid(process.pid),
                    signal.SIGTERM,
                )
            except ProcessLookupError:
                self._process = None
                return True

            try:
                process.wait(timeout=timeout)
                self._process = None
                return True
            except subprocess.TimeoutExpired:
                pass

            # Force termination if graceful shutdown timed out.
            try:
                os.killpg(
                    os.getpgid(process.pid),
                    signal.SIGKILL,
                )
            except ProcessLookupError:
                pass

            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                return False

            self._process = None
            return True

    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def is_running(self) -> bool:
        """Return True when the managed MT5 process is alive."""
        if self._process is None:
            return False

        if self._process.poll() is None:
            return True

        self._process = None
        return False

    def pid(self) -> int:
        """Return the current MT5 launcher PID."""
        if self._process is None:
            return 0

        if self._process.poll() is not None:
            self._process = None
            return 0

        return self._process.pid

    def restart(self) -> int:
        """Stop MT5 if running, then start it again."""
        self.stop()
        return self.start()

    def heartbeat(self) -> dict[str, object]:
        """
        Return a lightweight runtime health snapshot.
        """
        running = self.is_running()

        return {
            "running": running,
            "pid": self.pid() if running else 0,
            "terminal": str(self.terminal_path),
        }