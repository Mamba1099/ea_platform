from __future__ import annotations

from fastapi import FastAPI, HTTPException

from manager.ipc.config import IPC_ROOT
from manager.ipc.file_bridge import EAFileBridge
from manager.lifecycle import EALifecycleController
from manager.monitoring import EAMonitor
from manager.mt5_runtime import MT5Runtime
from manager.registry import create_registry


app = FastAPI(
    title="EA Management Platform",
    version="0.1.0",
)


# ============================================================
# PLATFORM COMPONENTS
# ============================================================

registry = create_registry()

runtime = MT5Runtime(
    terminal_path=(
        "/home/mamba/.wine/drive_c/"
        "Program Files/MetaTrader 5/terminal64.exe"
    ),
    wine_prefix="/home/mamba/.wine",
)

bridge = EAFileBridge(IPC_ROOT)

lifecycle = EALifecycleController(
    registry,
    runtime,
    bridge,
)

monitor = EAMonitor(
    registry,
    bridge,
    stale_after_seconds=10.0,
)


# ============================================================
# HELPERS
# ============================================================

def get_ea_or_404(ea_id: str):
    try:
        return registry.get(ea_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"EA not found: {ea_id}",
        ) from exc


def status_payload(ea_id: str) -> dict:
    get_ea_or_404(ea_id)

    monitor.refresh(ea_id)

    status = bridge.read_status(ea_id)
    health = monitor.health_dict(ea_id)
    registry_ea = registry.get(ea_id)

    return {
        "registry": {
            "ea_id": registry_ea.ea_id,
            "name": registry_ea.name,
            "version": registry_ea.version,
            "symbol": registry_ea.symbol,
            "magic_number": registry_ea.magic_number,
            "status": registry_ea.status,
            "enabled": registry_ea.enabled,
            "heartbeat": registry_ea.heartbeat,
        },
        "ea": (
            status.to_dict()
            if status is not None
            else None
        ),
        "health": health,
        "mt5": runtime.heartbeat(),
    }


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "name": "EA Management Platform",
        "version": "0.1.0",
        "status": "online",
    }


@app.get("/health")
def platform_health():
    return {
        "status": "online",
        "mt5": runtime.heartbeat(),
        "eas": monitor.health_all(),
    }


# ============================================================
# EA DISCOVERY
# ============================================================

@app.get("/api/eas")
def list_eas():
    return {
        "eas": [
            status_payload(ea.ea_id)
            for ea in registry.list_all()
        ]
    }


@app.get("/api/eas/{ea_id}")
def get_ea(ea_id: str):
    return status_payload(ea_id)


@app.get("/api/eas/{ea_id}/health")
def get_ea_health(ea_id: str):
    get_ea_or_404(ea_id)

    health = monitor.refresh(ea_id)

    return {
        "ea_id": ea_id,
        "health": {
            "ea_id": health.ea_id,
            "status": health.status,
            "enabled": health.enabled,
            "status_available": health.status_available,
            "file_age_seconds": health.file_age_seconds,
            "healthy": health.healthy,
            "stale": health.stale,
            "terminal_connected": health.terminal_connected,
            "message": health.message,
        },
    }


# ============================================================
# LIFECYCLE CONTROLS
# ============================================================

@app.post("/api/eas/{ea_id}/start")
def start_ea(ea_id: str):
    get_ea_or_404(ea_id)

    try:
        lifecycle.refresh_status(ea_id)
        ea = lifecycle.start(ea_id)

        monitor.refresh(ea_id)

        return {
            "success": True,
            "action": "START",
            "ea": status_payload(ea_id),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.post("/api/eas/{ea_id}/pause")
def pause_ea(ea_id: str):
    get_ea_or_404(ea_id)

    try:
        lifecycle.refresh_status(ea_id)
        ea = lifecycle.pause(ea_id)

        monitor.refresh(ea_id)

        return {
            "success": True,
            "action": "PAUSE",
            "ea": status_payload(ea_id),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.post("/api/eas/{ea_id}/resume")
def resume_ea(ea_id: str):
    get_ea_or_404(ea_id)

    try:
        lifecycle.refresh_status(ea_id)
        ea = lifecycle.resume(ea_id)

        monitor.refresh(ea_id)

        return {
            "success": True,
            "action": "RESUME",
            "ea": status_payload(ea_id),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.post("/api/eas/{ea_id}/close-basket")
def close_basket(ea_id: str):
    get_ea_or_404(ea_id)

    try:
        lifecycle.refresh_status(ea_id)
        ack = lifecycle.close_basket(ea_id)

        monitor.refresh(ea_id)

        return {
            "success": True,
            "action": "CLOSE_BASKET",
            "ack": ack.to_dict(),
            "ea": status_payload(ea_id),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@app.post("/api/eas/{ea_id}/stop")
def stop_ea(ea_id: str):
    get_ea_or_404(ea_id)

    try:
        lifecycle.refresh_status(ea_id)
        ea = lifecycle.stop(ea_id)

        monitor.refresh(ea_id)

        return {
            "success": True,
            "action": "STOP",
            "ea": status_payload(ea_id),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc