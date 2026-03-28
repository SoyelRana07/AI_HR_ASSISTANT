# backend/db.py
import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from env_config import get_required_env, load_project_env

load_project_env(__file__)


def _build_database_url():
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    required = get_required_env(["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"])
    db_user = required["DB_USER"]
    db_password = required["DB_PASSWORD"]
    db_host = required["DB_HOST"]
    db_port = required["DB_PORT"]
    db_name = required["DB_NAME"]

    encoded_password = quote_plus(db_password)

    return (
        f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    )


DATABASE_URL = _build_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)