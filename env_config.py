import os
from pathlib import Path
from typing import Dict, Iterable, List

from dotenv import load_dotenv


def _find_project_root(anchor_file: str):
    current = Path(anchor_file).resolve().parent

    for path in [current, *current.parents]:
        if (path / "requirements.txt").exists() and (path / "backend").exists():
            return path

    return current


def load_project_env(anchor_file: str):
    project_root = _find_project_root(anchor_file)
    env_candidates = [project_root / ".env", project_root / "backend" / ".env"]

    for env_file in env_candidates:
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)

    return project_root


def get_required_env(required_names: Iterable[str]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    missing = []

    for name in required_names:
        value = os.getenv(name)
        if value is None or value == "":
            missing.append(name)
        else:
            values[name] = value

    if missing:
        missing_csv = ", ".join(sorted(missing))
        raise RuntimeError(f"Missing required environment variables: {missing_csv}")

    return values


def inspect_env_groups(group_requirements: Dict[str, Iterable[str]]):
    groups = {}
    all_missing: List[str] = []

    for group_name, names in group_requirements.items():
        present = []
        missing = []

        for name in names:
            value = os.getenv(name)
            if value is None or value == "":
                missing.append(name)
                all_missing.append(name)
            else:
                present.append(name)

        groups[group_name] = {
            "present": sorted(present),
            "missing": sorted(missing),
            "ok": len(missing) == 0,
        }

    dedup_missing = sorted(set(all_missing))
    return {
        "ok": len(dedup_missing) == 0,
        "missing": dedup_missing,
        "groups": groups,
    }
