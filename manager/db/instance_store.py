from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from manager.db.models import EAInstance


class EAInstanceStore:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get(self, ea_id: str) -> EAInstance | None:
        with self.session_factory() as db:
            statement = select(EAInstance).where(EAInstance.ea_id == ea_id)

            return db.scalar(statement)

    def upsert_from_registry(self, instance) -> EAInstance:
        with self.session_factory() as db:
            statement = select(EAInstance).where(EAInstance.ea_id == instance.ea_id)

            row = db.scalar(statement)

            now = datetime.now(timezone.utc)

            if row is None:
                row = EAInstance(
                    ea_id=instance.ea_id,
                    name=instance.name,
                    version=instance.version,
                    symbol=instance.symbol,
                    magic_number=instance.magic_number,
                    status=instance.status,
                    enabled=instance.enabled,
                    last_seen=instance.heartbeat,
                    created_at=now,
                    updated_at=now,
                )

                db.add(row)

            else:
                row.name = instance.name
                row.version = instance.version
                row.symbol = instance.symbol
                row.magic_number = instance.magic_number

                row.status = instance.status
                row.enabled = instance.enabled

                if instance.heartbeat is not None:
                    row.last_seen = instance.heartbeat

                row.updated_at = now

            db.commit()
            db.refresh(row)

            return row

    def bootstrap_from_registry(self, registry) -> None:
        for instance in registry.list_all():
            self.upsert_from_registry(instance)

    def persist_status(
        self,
        ea_id: str,
        status: str,
        enabled: bool,
        last_seen: datetime | None = None,
    ) -> EAInstance | None:
        with self.session_factory() as db:
            statement = select(EAInstance).where(EAInstance.ea_id == ea_id)

            row = db.scalar(statement)

            if row is None:
                return None

            row.status = status
            row.enabled = enabled

            if last_seen is not None:
                row.last_seen = last_seen

            row.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(row)

            return row

    def list_all(self) -> list[EAInstance]:
        with self.session_factory() as db:
            statement = select(EAInstance).order_by(EAInstance.ea_id)

            return list(db.scalars(statement).all())

    def persist_version(
        self,
        ea_id: str,
        version: str,
    ) -> EAInstance | None:
        with self.session_factory() as db:
            statement = select(EAInstance).where(EAInstance.ea_id == ea_id)

            row = db.scalar(statement)

            if row is None:
                return None

            row.version = version
            row.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(row)

            return row
