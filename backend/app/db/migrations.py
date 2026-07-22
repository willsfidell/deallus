"""Alembic utilities for running migrations programmatically."""

import os
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text

from app.db.database import engine


def get_alembic_config() -> Config:
    """Get Alembic configuration."""
    # Locate alembic.ini in the backend directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_ini = os.path.join(backend_dir, "alembic.ini")
    
    config = Config(alembic_ini)
    # Set the sqlalchemy URL
    config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "postgresql://aidi:password@localhost:5432/aidi"))
    return config


def get_current_revision() -> str:
    """Get the current database revision."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
        row = result.fetchone()
        return row[0] if row else None


def get_head_revision() -> str:
    """Get the head revision."""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


def is_database_current() -> bool:
    """Check if database is at the latest revision."""
    current = get_current_revision()
    head = get_head_revision()
    return current == head
