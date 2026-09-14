from __future__ import annotations

import os

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from manager.db.database import Base
from manager.db.models import EAEvent, EAInstance

load_dotenv()

config = context.config

database_url = os.getenv("DIRECT_DATABASE_URL")

if not database_url:
    raise RuntimeError("DIRECT_DATABASE_URL is not configured.")

database_url = database_url.replace(
    "postgresql://",
    "postgresql+psycopg://",
    1,
)

config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%"),
)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
