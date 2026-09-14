from __future__ import annotations

from manager.artifacts.scanner import (
    EAArtifactScanner,
)
from manager.db.artifact_store import (
    EAArtifactStore,
)


class EAArtifactService:
    def __init__(
        self,
        store: EAArtifactStore,
        scanner: EAArtifactScanner,
    ):
        self.store = store
        self.scanner = scanner

    def register(
        self,
        ea_id: str,
        version: str,
        path: str,
    ):
        artifact = self.scanner.inspect(
            ea_id=ea_id,
            version=version,
            path=path,
        )

        existing = self.store.get_by_hash(
            ea_id,
            artifact["sha256"],
        )

        if existing is not None:
            return existing

        return self.store.create(
            ea_id=artifact["ea_id"],
            version=artifact["version"],
            filename=artifact["filename"],
            path=artifact["path"],
            sha256=artifact["sha256"],
            file_size=artifact["file_size"],
        )

    def list_for_ea(
        self,
        ea_id: str,
        limit: int = 100,
    ):
        return self.store.list_for_ea(
            ea_id,
            limit,
        )
