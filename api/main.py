from __future__ import annotations

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from manager.ipc.config import IPC_ROOT
from manager.ipc.file_bridge import EAFileBridge
from manager.lifecycle import EALifecycleController
from manager.monitoring import EAMonitor, EAMonitorWatchdog
from manager.mt5_runtime import MT5Runtime
from manager.db.event_store import EventStore
from manager.db.database import SessionLocal
from manager.db.instance_store import EAInstanceStore
from manager.db.deployment_store import EADeploymentStore
from manager.deployment.service import EADeploymentService, EADeploymentError
from manager.db.artifact_store import EAArtifactStore
from manager.artifacts.scanner import EAArtifactScanner
from manager.artifacts.service import EAArtifactService
from manager.db.installation_store import EAInstallationStore
from manager.installations.service import (
    EAInstallationError,
    EAInstallationService,
)
from pydantic import BaseModel
from manager.registry import create_registry


class EADeploymentRequest(BaseModel):
    artifact_id: int
    installation_id: int


class EAArtifactRequest(BaseModel):
    version: str
    path: str


class EAInstallationRequest(BaseModel):
    terminal_name: str
    terminal_path: str
    experts_directory: str
    executable_name: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[platform] synchronizing EA registry with database")

    instance_store.bootstrap_from_registry(registry)

    print("[platform] starting EA monitor watchdog")

    watchdog.start()

    try:
        yield
    finally:
        print("[platform] stopping EA monitor watchdog")
        watchdog.stop()


app = FastAPI(title="EA Management Platform", lifespan=lifespan)


# ============================================================
# PLATFORM COMPONENTS
# ============================================================

registry = create_registry()

runtime = MT5Runtime(
    terminal_path=(
        "/home/mamba/.wine/drive_c/" "Program Files/MetaTrader 5/terminal64.exe"
    ),
    wine_prefix="/home/mamba/.wine",
)

bridge = EAFileBridge(IPC_ROOT)
event_store = EventStore(SessionLocal)
instance_store = EAInstanceStore(SessionLocal)
artifact_store = EAArtifactStore(SessionLocal)
deployment_store = EADeploymentStore(SessionLocal)
installation_store = EAInstallationStore(SessionLocal)

lifecycle = EALifecycleController(
    registry,
    runtime,
    bridge,
)

monitor = EAMonitor(
    registry,
    bridge,
    runtime,
    stale_threshold=10.0,
)

deployment_service = EADeploymentService(
    registry=registry,
    lifecycle=lifecycle,
    bridge=bridge,
    artifact_store=artifact_store,
    installation_store=installation_store,
    deployment_store=deployment_store,
    instance_store=instance_store,
    event_store=event_store,
)

artifact_service = EAArtifactService(
    store=artifact_store,
    scanner=EAArtifactScanner(),
)

installation_service = EAInstallationService(
    registry=registry,
    store=installation_store,
)

watchdog = EAMonitorWatchdog(
    monitor,
    event_store,
    instance_store,
    interval_seconds=2.0,
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
        "ea": (status.to_dict() if status is not None else None),
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
    return {"eas": [status_payload(ea.ea_id) for ea in registry.list_all()]}


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


@app.get("/api/monitor")
def monitor_status():
    return {
        "watchdog_running": watchdog.is_running(),
        "interval_seconds": watchdog.interval_seconds,
        "eas": monitor.health_all(),
    }


@app.get("/api/eas/{ea_id}/events")
def get_ea_events(ea_id: str, limit: int = 100):
    get_ea_or_404(ea_id)

    limit = max(1, min(limit, 500))

    events = event_store.list_events(
        ea_id,
        limit=limit,
    )

    return {
        "ea_id": ea_id,
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "previous_status": event.previous_status,
                "current_status": event.current_status,
                "message": event.message,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    }


@app.get("/api/db/eas")
def get_persisted_eas():
    instances = instance_store.list_all()

    return {
        "count": len(instances),
        "eas": [
            {
                "id": instance.id,
                "ea_id": instance.ea_id,
                "name": instance.name,
                "version": instance.version,
                "symbol": instance.symbol,
                "magic_number": instance.magic_number,
                "status": instance.status,
                "enabled": instance.enabled,
                "last_seen": (
                    instance.last_seen.isoformat() if instance.last_seen else None
                ),
                "created_at": instance.created_at.isoformat(),
                "updated_at": instance.updated_at.isoformat(),
            }
            for instance in instances
        ],
    }


@app.post("/api/eas/{ea_id}/deploy")
def deploy_ea(
    ea_id: str,
    request: EADeploymentRequest,
):
    get_ea_or_404(ea_id)

    try:
        deployment = deployment_service.deploy(
            ea_id=ea_id,
            artifact_id=request.artifact_id,
            installation_id=request.installation_id,
        )

    except EADeploymentError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "success": True,
        "deployment": {
            "id": deployment.id,
            "ea_id": deployment.ea_id,
            "version": deployment.version,
            "status": deployment.status,
            "file_hash": deployment.file_hash,
            "started_at": deployment.started_at.isoformat(),
            "completed_at": (
                deployment.completed_at.isoformat() if deployment.completed_at else None
            ),
        },
    }


@app.get("/api/eas/{ea_id}/deployments/preflight")
def deployment_preflight(
    ea_id: str,
    artifact_id: int,
):
    get_ea_or_404(ea_id)

    return deployment_service.preflight(
        ea_id=ea_id,
        artifact_id=artifact_id,
    )


@app.get("/api/eas/{ea_id}/artifacts/{artifact_id}")
def get_ea_artifact(
    ea_id: str,
    artifact_id: int,
):
    get_ea_or_404(ea_id)

    artifact = artifact_store.get(artifact_id)

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    if artifact.ea_id != ea_id:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found for this EA.",
        )

    return {
        "id": artifact.id,
        "ea_id": artifact.ea_id,
        "version": artifact.version,
        "filename": artifact.filename,
        "path": artifact.path,
        "sha256": artifact.sha256,
        "file_size": artifact.file_size,
        "created_at": artifact.created_at.isoformat(),
    }


@app.get("/api/eas/{ea_id}/deployments")
def get_ea_deployments(
    ea_id: str,
    limit: int = 100,
):
    get_ea_or_404(ea_id)

    limit = max(1, min(limit, 500))

    deployments = deployment_store.list_for_ea(
        ea_id,
        limit,
    )

    return {
        "ea_id": ea_id,
        "deployments": [
            {
                "id": deployment.id,
                "version": deployment.version,
                "status": deployment.status,
                "source_path": deployment.source_path,
                "target_path": deployment.target_path,
                "file_hash": deployment.file_hash,
                "error_message": deployment.error_message,
                "started_at": (deployment.started_at.isoformat()),
                "completed_at": (
                    deployment.completed_at.isoformat()
                    if deployment.completed_at
                    else None
                ),
            }
            for deployment in deployments
        ],
    }


@app.post("/api/eas/{ea_id}/artifacts")
def register_artifact(
    ea_id: str,
    request: EAArtifactRequest,
):
    get_ea_or_404(ea_id)

    try:
        artifact = artifact_service.register(
            ea_id=ea_id,
            version=request.version,
            path=request.path,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "success": True,
        "artifact": {
            "id": artifact.id,
            "ea_id": artifact.ea_id,
            "version": artifact.version,
            "filename": artifact.filename,
            "path": artifact.path,
            "sha256": artifact.sha256,
            "file_size": artifact.file_size,
            "created_at": artifact.created_at.isoformat(),
        },
    }


@app.get("/api/eas/{ea_id}/artifacts")
def get_ea_artifacts(
    ea_id: str,
    limit: int = 100,
):
    get_ea_or_404(ea_id)

    limit = max(1, min(limit, 500))

    artifacts = artifact_service.list_for_ea(
        ea_id,
        limit,
    )

    return {
        "ea_id": ea_id,
        "artifacts": [
            {
                "id": artifact.id,
                "version": artifact.version,
                "filename": artifact.filename,
                "path": artifact.path,
                "sha256": artifact.sha256,
                "file_size": artifact.file_size,
                "created_at": artifact.created_at.isoformat(),
            }
            for artifact in artifacts
        ],
    }


@app.post("/api/eas/{ea_id}/installations")
def register_ea_installation(
    ea_id: str,
    request: EAInstallationRequest,
):
    get_ea_or_404(ea_id)

    try:
        installation = installation_service.register(
            ea_id=ea_id,
            terminal_name=request.terminal_name,
            terminal_path=request.terminal_path,
            experts_directory=request.experts_directory,
            executable_name=request.executable_name,
        )
    except EAInstallationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "success": True,
        "installation": {
            "id": installation.id,
            "ea_id": installation.ea_id,
            "terminal_name": installation.terminal_name,
            "terminal_path": installation.terminal_path,
            "experts_directory": installation.experts_directory,
            "executable_name": installation.executable_name,
            "active": installation.active,
            "created_at": installation.created_at.isoformat(),
        },
    }


@app.get("/api/eas/{ea_id}/installations")
def get_ea_installations(
    ea_id: str,
):
    get_ea_or_404(ea_id)

    installations = installation_service.list_for_ea(ea_id)

    return {
        "ea_id": ea_id,
        "installations": [
            {
                "id": item.id,
                "terminal_name": item.terminal_name,
                "terminal_path": item.terminal_path,
                "experts_directory": item.experts_directory,
                "executable_name": item.executable_name,
                "active": item.active,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            for item in installations
        ],
    }
