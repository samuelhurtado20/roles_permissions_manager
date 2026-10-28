import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.db.session import Base
from app.core.config import settings
from app.models.user import User  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.permission import Permission  # noqa: F401
from app.models.chat import ChatRecord  # noqa: F401

config = context.config

target_metadata = Base.metadata


def get_url():
    return settings.DATABASE_URL


def run_migrations_offline():
    url = get_url()
    context.config.set_main_option("sqlalchemy.url", url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        url=get_url(),
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