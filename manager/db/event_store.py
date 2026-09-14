from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from manager.db.models import EAEvent


class EventStore:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def record(
        self,
        ea_id: str,
        event_type: str,
        previous_status: str | None,
        current_status: str | None,
        message: str = "",
    ) -> EAEvent:
        with self.session_factory() as db:
            event = EAEvent(
                ea_id=ea_id,
                event_type=event_type,
                previous_status=previous_status,
                current_status=current_status,
                message=message,
            )

            db.add(event)
            db.commit()
            db.refresh(event)

            return event

    def list_events(
        self,
        ea_id: str,
        limit: int = 100,
    ) -> list[EAEvent]:
        with self.session_factory() as db:
            statement = (
                select(EAEvent)
                .where(EAEvent.ea_id == ea_id)
                .order_by(EAEvent.created_at.desc())
                .limit(limit)
            )

            return list(db.scalars(statement).all())
