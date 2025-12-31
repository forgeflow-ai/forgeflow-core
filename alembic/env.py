from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

import os
import sys

# app import path
sys.path.append(os.path.abspath("."))

from app.core.config import settings
from app.db.base import Base

# IMPORTANT: modellere import ver ki metadata dolsun
from app.models.user import User  # noqa: F401
from app.models.api_key import ApiKey  # noqa: F401
from app.models.workflow import Workflow  # noqa: F401
from app.models.workflow_version import WorkflowVersion  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.flow import Flow  # noqa: F401
from app.models.flow_run import FlowRun  # noqa: F401

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL

def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

