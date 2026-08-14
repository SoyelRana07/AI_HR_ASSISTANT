import json
from datetime import datetime
from typing import Any, Dict, Optional
from backend.db import engine, SessionLocal
from backend.models import Base, AuditLog


def _ensure_tables_created():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass


def log_audit_event(
    event_type: str,
    status: str,
    employee_id: Optional[int] = None,
    role: Optional[str] = None,
    tool_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    execution_time_ms: int = 0,
    details: Optional[Any] = None,
) -> Optional[int]:
    """Persist an audit record to PostgreSQL db safely without raising exceptions."""
    _ensure_tables_created()
    db = SessionLocal()
    try:
        params_str = json.dumps(parameters) if parameters else None
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)

        audit_entry = AuditLog(
            timestamp=datetime.utcnow(),
            employee_id=employee_id,
            role=role,
            event_type=event_type,
            tool_name=tool_name,
            parameters=params_str,
            status=status,
            execution_time_ms=execution_time_ms,
            details=details_str,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry.id
    except Exception as exc:
        db.rollback()
        print(f"Audit log write failed: {exc}")
        return None
    finally:
        db.close()
