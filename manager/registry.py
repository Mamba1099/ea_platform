from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class EAInstance:
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
    Registry for the EAs managed by the platform.

    At the moment the platform manages one EA:
        AI_BASKET_EA
    """

    def __init__(self) -> None:
        self._instances: dict[str, EAInstance] = {}

    def register(
        self,
        ea_id: str,
        name: str,
        version: str,
        symbol: str,
        magic_number: int,
    ) -> EAInstance:
        """Register a new EA instance."""

        if not ea_id.strip():
            raise ValueError("EA ID cannot be empty.")

        if ea_id in self._instances:
            raise ValueError(f"EA already registered: {ea_id}")

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

    def get(self, ea_id: str) -> EAInstance:
        """Return a registered EA."""

        instance = self._instances.get(ea_id)

        if instance is None:
            raise KeyError(f"EA not registered: {ea_id}")

        return instance

    def list_all(self) -> list[EAInstance]:
        """Return all registered EAs."""

        return list(self._instances.values())

    def set_status(self, ea_id: str, status: str) -> EAInstance:
        """Update the operational status of an EA."""

        instance = self.get(ea_id)
        instance.status = status
        return instance

    def set_enabled(self, ea_id: str, enabled: bool) -> EAInstance:
        """Enable or disable trading for an EA."""

        instance = self.get(ea_id)
        instance.enabled = enabled
        return instance

    def heartbeat(self, ea_id: str) -> EAInstance:
        """Record the latest heartbeat time."""

        instance = self.get(ea_id)
        instance.heartbeat = datetime.now(timezone.utc).isoformat()
        return instance

    def snapshot(self) -> list[dict]:
        """Return registry data in API-friendly form."""

        return [
            asdict(instance)
            for instance in self._instances.values()
        ]


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