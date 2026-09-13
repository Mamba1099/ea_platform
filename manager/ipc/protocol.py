from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional


class EACommand(str, Enum):
    START = "START"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    CLOSE_BASKET = "CLOSE_BASKET"
    STOP = "STOP"


class EAControlStatus(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    ERROR = "ERROR"


class CommandResult(str, Enum):
    RECEIVED = "RECEIVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class EACommandMessage:
    ea_id: str
    request_id: str
    command: EACommand
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["command"] = self.command.value
        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "EACommandMessage":
        return cls(
            ea_id=str(data["ea_id"]),
            request_id=str(data["request_id"]),
            command=EACommand(str(data["command"])),
            timestamp=str(data["timestamp"]),
        )


@dataclass(frozen=True)
class EACommandAck:
    ea_id: str
    request_id: str
    command: EACommand
    result: CommandResult
    timestamp: str
    message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["command"] = self.command.value
        data["result"] = self.result.value
        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "EACommandAck":
        return cls(
            ea_id=str(data["ea_id"]),
            request_id=str(data["request_id"]),
            command=EACommand(str(data["command"])),
            result=CommandResult(str(data["result"])),
            timestamp=str(data["timestamp"]),
            message=data.get("message"),
        )


@dataclass(frozen=True)
class EABasketStatus:
    state: str = "FLAT"
    direction: str = "NONE"
    positions: int = 0
    floating_pnl: float = 0.0
    thesis_score: float = 0.0
    recovery_score: float = 0.0
    opportunity_score: float = 0.0


@dataclass(frozen=True)
class EAStatusMessage:
    ea_id: str
    name: str
    version: str
    symbol: str
    magic_number: int

    status: EAControlStatus
    enabled: bool

    timestamp: str

    terminal_connected: bool = False

    basket: Optional[EABasketStatus] = None

    last_request_id: Optional[str] = None
    last_command_result: Optional[CommandResult] = None
    last_command_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        data["status"] = self.status.value

        if self.last_command_result is not None:
            data["last_command_result"] = self.last_command_result.value

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "EAStatusMessage":
        basket_data = data.get("basket")

        basket = None

        if basket_data is not None:
            basket = EABasketStatus(
                state=str(basket_data.get("state", "FLAT")),
                direction=str(basket_data.get("direction", "NONE")),
                positions=int(basket_data.get("positions", 0)),
                floating_pnl=float(basket_data.get("floating_pnl", 0.0)),
                thesis_score=float(basket_data.get("thesis_score", 0.0)),
                recovery_score=float(basket_data.get("recovery_score", 0.0)),
                opportunity_score=float(basket_data.get("opportunity_score", 0.0)),
            )

        result = data.get("last_command_result")

        return cls(
            ea_id=str(data["ea_id"]),
            name=str(data["name"]),
            version=str(data["version"]),
            symbol=str(data["symbol"]),
            magic_number=int(data["magic_number"]),
            status=EAControlStatus(str(data["status"])),
            enabled=bool(data["enabled"]),
            timestamp=str(data["timestamp"]),
            terminal_connected=bool(data.get("terminal_connected", False)),
            basket=basket,
            last_request_id=data.get("last_request_id"),
            last_command_result=(
                CommandResult(str(result)) if result is not None else None
            ),
            last_command_message=data.get("last_command_message"),
        )
