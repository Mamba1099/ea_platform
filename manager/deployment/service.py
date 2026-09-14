from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path

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
        deployment_store: EADeploymentStore,
        instance_store: EAInstanceStore,
        event_store: EventStore,
    ):
        self.registry = registry
        self.lifecycle = lifecycle
        self.bridge = bridge
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

    def _resolve_target(self, target: Path) -> Path:
        if target.is_symlink():
            return target.resolve()

        return target

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

    def deploy(
        self,
        ea_id: str,
        version: str,
        source_path: str,
        target_path: str,
    ):
        source = Path(source_path).expanduser().resolve()
        requested_target = Path(target_path).expanduser()
        target = self._resolve_target(requested_target)

        instance = self.registry.get(ea_id)

        if instance is None:
            raise EADeploymentError(f"Unknown EA: {ea_id}")

        if not source.is_file():
            raise EADeploymentError(f"Source EX5 does not exist: {source}")

        if source.suffix.lower() != ".ex5":
            raise EADeploymentError("Deployment source must be an .ex5 file.")

        # Read the live EA status before doing anything.
        live_status = self.bridge.read_status(ea_id)

        if live_status is None:
            raise EADeploymentError(
                "EA telemetry is unavailable. " "Deployment aborted."
            )

        # Never restart an EA that currently owns a basket.
        if live_status.basket.positions > 0:
            raise EADeploymentError(
                f"Deployment blocked: EA has "
                f"{live_status.basket.positions} open positions."
            )

        file_hash = self.calculate_sha256(source)

        deployment = self.deployment_store.create(
            ea_id=ea_id,
            version=version,
            source_path=str(source),
            target_path=str(target),
            file_hash=file_hash,
        )

        backup: Path | None = None

        try:
            self.deployment_store.mark_deploying(deployment.id)

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            same_physical_file = False

            try:
                same_physical_file = source.samefile(target)
            except FileNotFoundError:
                same_physical_file = False

            # Backup the currently installed EX5.
            if target.exists():
                timestamp = int(time.time())

                backup = target.with_name(f"{target.name}.{timestamp}.bak")

                shutil.copy2(
                    target,
                    backup,
                )
            # only copy when source and target are different
            if not same_physical_file:
                shutil.copy2(source, target)

            # restart MT5/EA
            self.lifecycle.stop(ea_id)
            self.lifecycle.start(ea_id)

            status = self._wait_for_version(ea_id, version)

            self.registry.set_version(ea_id, version)

            self.instance_store.persist_version(ea_id, version)

            self.event_store.record(
                ea_id=ea_id,
                event_type="EA_DEPLOYED",
                previous_status=live_status.status,
                current_status=status.status,
                message=(f"EA version {version} deployed and", f"Verified succesfully"),
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
