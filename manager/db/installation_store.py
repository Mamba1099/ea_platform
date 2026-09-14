from __future__ import annotations

from sqlalchemy import select

from manager.db.models import EAInstallation


class EAInstallationStore:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create(
        self,
        ea_id: str,
        terminal_name: str,
        terminal_path: str,
        experts_directory: str,
        executable_name: str,
    ) -> EAInstallation:
        with self.session_factory() as db:
            installation = EAInstallation(
                ea_id=ea_id,
                terminal_name=terminal_name,
                terminal_path=terminal_path,
                experts_directory=experts_directory,
                executable_name=executable_name,
                active=True,
            )

            db.add(installation)
            db.commit()
            db.refresh(installation)

            return installation

    def get(
        self,
        installation_id: int,
    ) -> EAInstallation | None:
        with self.session_factory() as db:
            return db.get(
                EAInstallation,
                installation_id,
            )

    def list_for_ea(
        self,
        ea_id: str,
    ) -> list[EAInstallation]:
        with self.session_factory() as db:
            statement = (
                select(EAInstallation)
                .where(EAInstallation.ea_id == ea_id)
                .order_by(EAInstallation.id)
            )

            return list(db.scalars(statement).all())

    def active_for_ea(
        self,
        ea_id: str,
    ) -> EAInstallation | None:
        with self.session_factory() as db:
            statement = (
                select(EAInstallation)
                .where(
                    EAInstallation.ea_id == ea_id,
                    EAInstallation.active.is_(True),
                )
                .order_by(EAInstallation.id)
                .limit(1)
            )

            return db.scalar(statement)

    def deactivate(
        self,
        installation_id: int,
    ) -> EAInstallation | None:
        with self.session_factory() as db:
            installation = db.get(
                EAInstallation,
                installation_id,
            )

            if installation is None:
                return None

            installation.active = False

            db.commit()
            db.refresh(installation)

            return installation
