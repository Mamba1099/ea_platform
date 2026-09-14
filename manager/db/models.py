from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from manager.db.database import Base


class EAInstance(Base):
    __tablename__ = "ea_instances"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ea_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    magic_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="STOPPED",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class EAEvent(Base):
    __tablename__ = "ea_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ea_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    previous_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    current_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class EADeployment(Base):
    __tablename__ = "ea_deployments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ea_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    target_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    file_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class EAArtifact(Base):
    __tablename__ = "ea_artifacts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ea_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "ea_id",
            "version",
            "sha256",
            name="uq_ea_artifact_version_hash",
        ),
    )


class EAInstallation(Base):
    __tablename__ = "ea_installations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    ea_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    terminal_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    terminal_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    experts_directory: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    executable_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
