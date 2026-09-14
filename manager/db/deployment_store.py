from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from manager.db.models import EADeployment


class EADeploymentStore:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create(
        self,
        ea_id: str,
        version: str,
        source_path: str,
        target_path: str,
        file_hash: str,
    ) -> EADeployment:
        with self.session_factory() as db:
            deployment = EADeployment(
                ea_id=ea_id,
                version=version,
                source_path=source_path,
                target_path=target_path,
                file_hash=file_hash,
                status="PENDING",
                started_at=datetime.now(timezone.utc),
            )

            db.add(deployment)
            db.commit()
            db.refresh(deployment)

            return deployment

    def mark_deploying(
        self,
        deployment_id: int,
    ) -> EADeployment | None:
        return self._set_status(
            deployment_id,
            "DEPLOYING",
        )

    def mark_applied(
        self,
        deployment_id: int,
    ) -> EADeployment | None:
        with self.session_factory() as db:
            deployment = db.get(
                EADeployment,
                deployment_id,
            )

            if deployment is None:
                return None

            deployment.status = "APPLIED"
            deployment.completed_at = datetime.now(timezone.utc)
            deployment.error_message = None

            db.commit()
            db.refresh(deployment)

            return deployment

    def mark_failed(
        self,
        deployment_id: int,
        error_message: str,
    ) -> EADeployment | None:
        with self.session_factory() as db:
            deployment = db.get(
                EADeployment,
                deployment_id,
            )

            if deployment is None:
                return None

            deployment.status = "FAILED"
            deployment.completed_at = datetime.now(timezone.utc)
            deployment.error_message = error_message

            db.commit()
            db.refresh(deployment)

            return deployment

    def get(
        self,
        deployment_id: int,
    ) -> EADeployment | None:
        with self.session_factory() as db:
            return db.get(
                EADeployment,
                deployment_id,
            )

    def list_for_ea(
        self,
        ea_id: str,
        limit: int = 100,
    ) -> list[EADeployment]:
        with self.session_factory() as db:
            statement = (
                select(EADeployment)
                .where(EADeployment.ea_id == ea_id)
                .order_by(EADeployment.id.desc())
                .limit(limit)
            )

            return list(db.scalars(statement).all())

    def _set_status(
        self,
        deployment_id: int,
        status: str,
    ) -> EADeployment | None:
        with self.session_factory() as db:
            deployment = db.get(
                EADeployment,
                deployment_id,
            )

            if deployment is None:
                return None

            deployment.status = status

            db.commit()
            db.refresh(deployment)

            return deployment
