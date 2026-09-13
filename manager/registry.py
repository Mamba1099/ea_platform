from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class EAInstance:
    """
    Represents one EA registered with the management platform.
    """

    ea_id: str
    name: str
    version: str
    symbol: str
    magic_number: int

    status: str = "STOPPED"
    enabled: bool = False
    heartbeat: Optional[str] = None


class EARegistry:
    """
    Central in-memory registry of managed EA instances.

    The registry stores platform-side state only.
    It does not communicate with MT5 or the EA itself.
    """

    def __init__(self) -> None:
        self._instances: dict[str, EAInstance] = {}

    # =========================================================
    # REGISTRATION
    # =========================================================

    def register(
        self,
        ea_id: str,
        name: str,
        version: str,
        symbol: str,
        magic_number: int,
    ) -> EAInstance:
        """
        Register a new EA instance.
        """

        if not ea_id.strip():
            raise ValueError("EA ID cannot be empty.")

        if ea_id in self._instances:
            raise ValueError(f"EA already registered: {ea_id}")

        if not name.strip():
            raise ValueError("EA name cannot be empty.")

        if not symbol.strip():
            raise ValueError("EA symbol cannot be empty.")

        if magic_number <= 0:
            raise ValueError("Magic number must be greater than zero.")

        instance = EAInstance(
            ea_id=ea_id,
            name=name,
            version=version,
            symbol=symbol,
            magic_number=magic_number,
        )

        self._instances[ea_id] = instance

        return instance

    # =========================================================
    # LOOKUP
    # =========================================================

    def get(
        self,
        ea_id: str,
    ) -> EAInstance:
        """
        Return a registered EA.
        """

        instance = self._instances.get(ea_id)

        if instance is None:
            raise KeyError(f"EA not registered: {ea_id}")

        return instance

    def exists(
        self,
        ea_id: str,
    ) -> bool:
        """
        Return True when an EA is registered.
        """

        return ea_id in self._instances

    def list_all(self) -> list[EAInstance]:
        """
        Return all registered EA instances.
        """

        return list(self._instances.values())

    # =========================================================
    # STATE
    # =========================================================

    def set_status(
        self,
        ea_id: str,
        status: str,
    ) -> EAInstance:
        """
        Update the platform-side operational status.
        """

        instance = self.get(ea_id)
        instance.status = status

        return instance

    def set_enabled(
        self,
        ea_id: str,
        enabled: bool,
    ) -> EAInstance:
        """
        Update whether the EA is enabled for trading.
        """

        instance = self.get(ea_id)
        instance.enabled = enabled

        return instance

    def heartbeat(
        self,
        ea_id: str,
    ) -> EAInstance:
        """
        Record a platform-side heartbeat timestamp.
        """

        instance = self.get(ea_id)

        instance.heartbeat = datetime.now(timezone.utc).isoformat()

        return instance

    # =========================================================
    # SNAPSHOT
    # =========================================================

    def snapshot(self) -> list[dict]:
        """
        Return registry state in API-friendly form.
        """

        return [asdict(instance) for instance in self._instances.values()]


# =============================================================
# INITIAL REGISTRY
# =============================================================


def create_registry() -> EARegistry:
    """
    Create the platform registry and register
    the currently deployed EA.
    """

    registry = EARegistry()

    registry.register(
        ea_id="AI_BASKET_EA",
        name="AI Basket EA",
        version="1.31",
        symbol="XAUUSD.m",
        magic_number=26091001,
    )

    return registry
