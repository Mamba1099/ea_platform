from __future__ import annotations

from sqlalchemy import select

from manager.db.models import EAArtifact


class EAArtifactStore:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create(
        self,
        ea_id: str,
        version: str,
        filename: str,
        path: str,
        sha256: str,
        file_size: int,
    ) -> EAArtifact:
        with self.session_factory() as db:
            artifact = EAArtifact(
                ea_id=ea_id,
                version=version,
                filename=filename,
                path=path,
                sha256=sha256,
                file_size=file_size,
            )

            db.add(artifact)
            db.commit()
            db.refresh(artifact)

            return artifact

    def get(
        self,
        artifact_id: int,
    ) -> EAArtifact | None:
        with self.session_factory() as db:
            return db.get(EAArtifact, artifact_id)

    def get_by_version(
        self,
        ea_id: str,
        version: str,
    ) -> EAArtifact | None:
        with self.session_factory() as db:
            statement = (
                select(EAArtifact)
                .where(
                    EAArtifact.ea_id == ea_id,
                    EAArtifact.version == version,
                )
                .order_by(EAArtifact.id.desc())
            )

            return db.scalar(statement)

    def get_by_hash(
        self,
        ea_id: str,
        sha256: str,
    ) -> EAArtifact | None:
        with self.session_factory() as db:
            statement = (
                select(EAArtifact)
                .where(
                    EAArtifact.ea_id == ea_id,
                    EAArtifact.sha256 == sha256,
                )
                .order_by(EAArtifact.id.desc())
            )

            return db.scalar(statement)

    def list_for_ea(
        self,
        ea_id: str,
        limit: int = 100,
    ) -> list[EAArtifact]:
        with self.session_factory() as db:
            statement = (
                select(EAArtifact)
                .where(EAArtifact.ea_id == ea_id)
                .order_by(EAArtifact.id.desc())
                .limit(limit)
            )

            return list(db.scalars(statement).all())
