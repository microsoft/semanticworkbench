import asyncio
import logging

import semantic_workbench_service
from alembic import context
from rich.logging import RichHandler
from semantic_workbench_service.db import (
    ensure_async_driver_scheme,
)
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config
from sqlmodel import SQLModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_db_url() -> str:
    url = semantic_workbench_service.settings.db.url
    return ensure_async_driver_scheme(url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    url = semantic_workbench_service.settings.db.url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def async_run_migrations_online(connectable) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    async with connectable.connect() as connection:
        await connection.run_sync(run_migrations)

    await connectable.dispose()


def connect() -> AsyncEngine:
    url = get_db_url()
    config_section = config.get_section(config.config_ini_section, {})
    config_section["sqlalchemy.url"] = url
    return async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )


def run_migrations_online():
    if len(logging.root.handlers) == 0:
        logging.basicConfig(
            level=logging.INFO,
            format="%(name)s | %(message)s",
            datefmt="[%X]",
            handlers=[RichHandler()],
        )
        logging.getLogger("sqlalchemy").setLevel(logging.INFO)

    logging.getLogger("alembic").setLevel(logging.INFO)

    connectable = config.attributes.get("connection", None)
    if connectable is None:
        connectable = connect()

    if isinstance(connectable, AsyncEngine):
        return asyncio.run(async_run_migrations_online(connectable))

    run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
