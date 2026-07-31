"""Alembic environment bound to ShopLens' validated database URL."""

from logging.config import fileConfig

from alembic import context
from app.core.settings import Settings
from app.db import models as database_models  # noqa: F401
from app.db.base import Base
from app.db.session import sqlalchemy_database_url
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = Settings()
config.set_main_option("sqlalchemy.url", sqlalchemy_database_url(str(settings.database_url)))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL without creating an Engine."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations transactionally through psycopg 3."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
