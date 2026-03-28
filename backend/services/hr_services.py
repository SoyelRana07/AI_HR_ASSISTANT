# backend/services/hr_service.py

from backend.db import SessionLocal
from backend.models import Leave
from backend.repository.leave_repo import get_leave_balance as get_repo_leave_balance

def get_leave_balance(employee_id: int):
    return get_repo_leave_balance(employee_id)


def apply_leave(employee_id: int, date: str):
    db = SessionLocal()
    try:
        leave = db.query(Leave).filter_by(employee_id=employee_id).first()

        if not leave:
            return {"status": "failed", "reason": "Employee not found"}

        if leave.remaining <= 0:
            return {"status": "failed", "reason": "No leaves left"}

        leave.used += 1
        leave.remaining -= 1
        db.commit()

        return {"status": "success", "message": f"Leave applied for {date}"}
    finally:
        db.close()