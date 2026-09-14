from __future__ import annotations

from pathlib import Path

from manager.db.installation_store import EAInstallationStore
from manager.registry import EARegistry


class EAInstallationError(RuntimeError):
    pass


class EAInstallationService:
    def __init__(
        self,
        registry: EARegistry,
        store: EAInstallationStore,
    ):
        self.registry = registry
        self.store = store

    def register(
        self,
        ea_id: str,
        terminal_name: str,
        terminal_path: str,
        experts_directory: str,
        executable_name: str,
    ):
        if self.registry.get(ea_id) is None:
            raise EAInstallationError(f"Unknown EA: {ea_id}")

        terminal = Path(terminal_path).expanduser().resolve()

        experts = Path(experts_directory).expanduser().resolve()

        if not executable_name.lower().endswith(".ex5"):
            raise EAInstallationError("Executable must be an .ex5 file.")

        return self.store.create(
            ea_id=ea_id,
            terminal_name=terminal_name,
            terminal_path=str(terminal),
            experts_directory=str(experts),
            executable_name=executable_name,
        )

    @staticmethod
    def executable_path(
        installation,
    ) -> Path:
        return Path(installation.experts_directory) / installation.executable_name

    def get(
        self,
        installation_id: int,
    ):
        return self.store.get(installation_id)

    def list_for_ea(
        self,
        ea_id: str,
    ):
        return self.store.list_for_ea(ea_id)

    def active_for_ea(
        self,
        ea_id: str,
    ):
        return self.store.active_for_ea(ea_id)
