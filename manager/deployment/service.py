from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path

from manager.db.artifact_store import EAArtifactStore
from manager.db.deployment_store import EADeploymentStore
from manager.db.event_store import EventStore
from manager.db.instance_store import EAInstanceStore
from manager.ipc.file_bridge import EAFileBridge
from manager.lifecycle import EALifecycleController
from manager.registry import EARegistry


class EADeploymentError(RuntimeError):
    pass


class EADeploymentService:
    def __init__(
        self,
        registry: EARegistry,
        lifecycle: EALifecycleController,
        bridge: EAFileBridge,
        artifact_store: EAArtifactStore,
        deployment_store: EADeploymentStore,
        instance_store: EAInstanceStore,
        event_store: EventStore,
    ):
        self.registry = registry
        self.lifecycle = lifecycle
        self.bridge = bridge
        self.artifact_store = artifact_store
        self.deployment_store = deployment_store
        self.instance_store = instance_store
        self.event_store = event_store

    @staticmethod
    def calculate_sha256(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    def _wait_for_version(
        self,
        ea_id: str,
        expected_version: str,
        timeout: float = 30.0,
    ):
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            status = self.bridge.read_status(ea_id)

            if status is not None:
                if status.version == expected_version:
                    return status

            time.sleep(0.5)

        raise EADeploymentError(
            f"EA did not report version {expected_version} "
            f"within {timeout:.0f} seconds."
        )

    def preflight(
        self,
        ea_id: str,
        artifact_id: int,
    ) -> dict:
        instance = self.registry.get(ea_id)

        if instance is None:
            return {
                "allowed": False,
                "reason": f"Unknown EA: {ea_id}",
                "ea_status": None,
                "positions": None,
                "terminal_connected": False,
                "artifact_available": False,
                "artifact_hash_valid": False,
            }

        artifact = self.artifact_store.get(artifact_id)

        if artifact is None:
            return {
                "allowed": False,
                "reason": f"Artifact {artifact_id} does not exist.",
                "ea_status": instance.status,
                "positions": None,
                "terminal_connected": False,
                "artifact_available": False,
                "artifact_hash_valid": False,
            }

        if artifact.ea_id != ea_id:
            return {
                "allowed": False,
                "reason": (
                    f"Artifact {artifact_id} belongs to "
                    f"{artifact.ea_id}, not {ea_id}."
                ),
                "ea_status": instance.status,
                "positions": None,
                "terminal_connected": False,
                "artifact_available": False,
                "artifact_hash_valid": False,
            }

        artifact_path = Path(artifact.path).expanduser().resolve()

        artifact_available = (
            artifact_path.is_file() and artifact_path.suffix.lower() == ".ex5"
        )

        if not artifact_available:
            return {
                "allowed": False,
                "reason": (f"Artifact file is unavailable: " f"{artifact_path}"),
                "ea_status": instance.status,
                "positions": None,
                "terminal_connected": False,
                "artifact_available": False,
                "artifact_hash_valid": False,
                "artifact": {
                    "id": artifact.id,
                    "version": artifact.version,
                },
            }

        current_hash = self.calculate_sha256(artifact_path)

        artifact_hash_valid = current_hash == artifact.sha256

        if not artifact_hash_valid:
            return {
                "allowed": False,
                "reason": (
                    "Artifact hash mismatch. " "The file changed after registration."
                ),
                "ea_status": instance.status,
                "positions": None,
                "terminal_connected": False,
                "artifact_available": True,
                "artifact_hash_valid": False,
                "artifact": {
                    "id": artifact.id,
                    "version": artifact.version,
                },
            }

        live_status = self.bridge.read_status(ea_id)

        if live_status is None:
            return {
                "allowed": False,
                "reason": "EA telemetry is unavailable.",
                "ea_status": instance.status,
                "positions": None,
                "terminal_connected": False,
                "artifact_available": True,
                "artifact_hash_valid": True,
                "artifact": {
                    "id": artifact.id,
                    "version": artifact.version,
                },
            }

        positions = live_status.basket.positions
        terminal_connected = bool(live_status.terminal_connected)

        if not terminal_connected:
            return {
                "allowed": False,
                "reason": "MT5 terminal is not connected.",
                "ea_status": live_status.status,
                "positions": positions,
                "terminal_connected": False,
                "artifact_available": True,
                "artifact_hash_valid": True,
                "artifact": {
                    "id": artifact.id,
                    "version": artifact.version,
                },
            }

        if positions > 0:
            return {
                "allowed": False,
                "reason": (
                    f"EA has {positions} open "
                    f"position(s). Close the basket before deployment."
                ),
                "ea_status": live_status.status,
                "positions": positions,
                "terminal_connected": True,
                "artifact_available": True,
                "artifact_hash_valid": True,
                "artifact": {
                    "id": artifact.id,
                    "version": artifact.version,
                },
            }

        return {
            "allowed": True,
            "reason": "EA is ready for deployment.",
            "ea_status": live_status.status,
            "positions": positions,
            "terminal_connected": terminal_connected,
            "artifact_available": artifact_available,
            "artifact_hash_valid": artifact_hash_valid,
            "artifact": {
                "id": artifact.id,
                "version": artifact.version,
                "filename": artifact.filename,
                "sha256": artifact.sha256,
                "file_size": artifact.file_size,
            },
        }

    def deploy(
        self,
        ea_id: str,
        artifact_id: int,
    ):
        instance = self.registry.get(ea_id)

        if instance is None:
            raise EADeploymentError(f"Unknown EA: {ea_id}")

        artifact = self.artifact_store.get(artifact_id)

        if artifact is None:
            raise EADeploymentError(f"Artifact {artifact_id} does not exist.")

        if artifact.ea_id != ea_id:
            raise EADeploymentError(
                f"Artifact {artifact_id} belongs to " f"{artifact.ea_id}, not {ea_id}."
            )

        source = Path(artifact.path).expanduser().resolve()

        if not source.is_file():
            raise EADeploymentError(f"Artifact file does not exist: {source}")

        if source.suffix.lower() != ".ex5":
            raise EADeploymentError("Registered artifact is not an .ex5 file.")

        current_hash = self.calculate_sha256(source)

        if current_hash != artifact.sha256:
            raise EADeploymentError(
                "Artifact hash mismatch. The registered artifact "
                "has changed since it was stored."
            )

        # Read live EA status before doing anything.
        live_status = self.bridge.read_status(ea_id)

        if live_status is None:
            raise EADeploymentError("EA telemetry is unavailable. Deployment aborted.")

        # Never restart an EA with active positions.
        if live_status.basket.positions > 0:
            raise EADeploymentError(
                f"Deployment blocked: EA has "
                f"{live_status.basket.positions} open positions."
            )

        target = source

        deployment = self.deployment_store.create(
            ea_id=ea_id,
            version=artifact.version,
            source_path=str(source),
            target_path=str(target),
            file_hash=artifact.sha256,
        )

        backup: Path | None = None

        try:
            self.deployment_store.mark_deploying(deployment.id)

            # Backup the currently installed artifact.
            if target.exists():
                timestamp = int(time.time())

                backup = target.with_name(f"{target.name}.{timestamp}.bak")

                shutil.copy2(
                    target,
                    backup,
                )

            if not source.samefile(target):
                shutil.copy2(
                    source,
                    target,
                )

            # Restart MT5 / EA.
            self.lifecycle.stop(ea_id)
            self.lifecycle.start(ea_id)

            status = self._wait_for_version(
                ea_id,
                artifact.version,
            )

            self.registry.set_version(
                ea_id,
                artifact.version,
            )

            self.instance_store.persist_version(
                ea_id,
                artifact.version,
            )

            self.event_store.record(
                ea_id=ea_id,
                event_type="EA_DEPLOYED",
                previous_status=live_status.status,
                current_status=status.status,
                message=(
                    f"EA version {artifact.version} "
                    f"deployed and verified successfully."
                ),
            )

            return self.deployment_store.mark_applied(deployment.id)

        except Exception as exc:
            if backup is not None and backup.exists():
                try:
                    self.lifecycle.stop(ea_id)

                    shutil.copy2(
                        backup,
                        target,
                    )

                    self.lifecycle.start(ea_id)

                except Exception:
                    pass

            self.deployment_store.mark_failed(
                deployment.id,
                str(exc),
            )

            raise EADeploymentError(f"Deployment failed: {exc}") from exc
