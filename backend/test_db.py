# test_db.py

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine


def _load_env_files():
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent

    for env_file in (project_root / ".env", backend_dir / ".env"):
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)


def _require_env(name: str):
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"{name} is required")
    return value


_load_env_files()
DATABASE_URL = _require_env("DATABASE_URL")

engine = create_engine(DATABASE_URL)

try:
    conn = engine.connect()
    print("✅ Connected successfully!")
    conn.close()
except Exception as e:
    print("❌ Error:", e)