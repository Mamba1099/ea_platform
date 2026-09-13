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

    The Wine launcher process may terminate after handing execution
    to the actual terminal64.exe process, so runtime detection is
    based on the MT5 process itself.
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
        self.wine_prefix = Path(wine_prefix).expanduser() if wine_prefix else None
        self.startup_timeout = startup_timeout

        self._launcher_process: Optional[subprocess.Popen] = None
        self._lock = Lock()

    def _validate_terminal(self) -> None:
        if not self.terminal_path.exists():
            raise MT5RuntimeError(f"MT5 terminal not found: {self.terminal_path}")

        if not self.terminal_path.is_file():
            raise MT5RuntimeError(
                f"MT5 terminal path is not a file: {self.terminal_path}"
            )

    def _build_environment(self) -> dict[str, str]:
        env = os.environ.copy()

        if self.wine_prefix is not None:
            env["WINEPREFIX"] = str(self.wine_prefix)

        return env

    def _find_terminal_pid(self) -> int:
        """
        Find the actual terminal64.exe process.

        Wine may expose the Windows executable through
        wineserver/wine-preloader, so we inspect the full
        process command line.
        """

        try:
            result = subprocess.run(
                [
                    "pgrep",
                    "-af",
                    "terminal64.exe",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return 0

        if result.returncode != 0:
            return 0

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line:
                continue

            parts = line.split(maxsplit=1)

            if len(parts) != 2:
                continue

            try:
                pid = int(parts[0])
            except ValueError:
                continue

            command_line = parts[1]

            if command_line.lower().endswith("terminal64.exe"):
                return pid

        return 0

    def _launcher_alive(self) -> bool:
        return (
            self._launcher_process is not None and self._launcher_process.poll() is None
        )

    def start(self) -> int:
        """
        Start MetaTrader 5 under Wine.

        Returns:
            PID of the actual terminal64.exe process.
        """

        with self._lock:
            existing_pid = self._find_terminal_pid()

            if existing_pid > 0:
                return existing_pid

            self._validate_terminal()

            command = [
                self.wine_binary,
                str(self.terminal_path),
            ]

            try:
                self._launcher_process = subprocess.Popen(
                    command,
                    cwd=str(self.terminal_path.parent),
                    env=self._build_environment(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except OSError as exc:
                self._launcher_process = None

                raise MT5RuntimeError(
                    f"Failed to launch MT5 through Wine: {exc}"
                ) from exc

            deadline = time.monotonic() + self.startup_timeout

            while time.monotonic() < deadline:
                terminal_pid = self._find_terminal_pid()

                if terminal_pid > 0:
                    return terminal_pid
                time.sleep(0.25)

            launcher_code = (
                self._launcher_process.poll()
                if self._launcher_process is not None
                else None
            )

            self._launcher_process = None

            raise MT5RuntimeError(
                "MT5 terminal64.exe was not detected within "
                f"{self.startup_timeout:.1f} seconds. "
                f"Wine launcher exit code: {launcher_code}"
            )

    def stop(self, timeout: float = 10.0) -> bool:
        """
        Stop the actual MT5 terminal process.

        Returns:
            True if MT5 stopped successfully.
        """

        with self._lock:
            terminal_pid = self._find_terminal_pid()

            if terminal_pid <= 0:
                self._launcher_process = None
                return True

            try:
                os.kill(
                    terminal_pid,
                    signal.SIGTERM,
                )
            except ProcessLookupError:
                self._launcher_process = None
                return True

            deadline = time.monotonic() + timeout

            while time.monotonic() < deadline:
                if self._find_terminal_pid() <= 0:
                    self._launcher_process = None
                    return True

                time.sleep(0.25)

            try:
                os.kill(
                    terminal_pid,
                    signal.SIGKILL,
                )
            except ProcessLookupError:
                pass

            deadline = time.monotonic() + 3.0

            while time.monotonic() < deadline:
                if self._find_terminal_pid() <= 0:
                    self._launcher_process = None
                    return True

                time.sleep(0.25)

            return False

    def is_running(self) -> bool:
        """Return True when terminal64.exe is running."""
        return self._find_terminal_pid() > 0

    def pid(self) -> int:
        """Return the actual terminal64.exe PID."""
        return self._find_terminal_pid()

    def restart(self) -> int:
        """Stop MT5 and start it again."""
        self.stop()
        return self.start()

    def heartbeat(self) -> dict[str, object]:
        """Return a lightweight MT5 runtime health snapshot."""

        terminal_pid = self._find_terminal_pid()

        return {
            "running": terminal_pid > 0,
            "pid": terminal_pid,
            "terminal": str(self.terminal_path),
        }
