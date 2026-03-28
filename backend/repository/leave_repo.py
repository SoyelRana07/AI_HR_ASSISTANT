from backend.db import SessionLocal
from backend.models import Employee, LeaveBalance
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

def get_leave_balance(employee_id: int):
    db = SessionLocal()

    try:
        record = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id
        ).first()

        if not record:
            return {"error": "Employee not found"}

        return {
            "total": record.total,
            "used": record.used,
            "remaining": record.remaining
        }
    except SQLAlchemyError:
        return {"error": "Database unavailable"}

    finally:
        db.close()


def get_team_leave_summary():
    db = SessionLocal()

    try:
        employee_count, total_allocated, total_used, total_remaining, avg_remaining = (
            db.query(
                func.count(LeaveBalance.employee_id),
                func.coalesce(func.sum(LeaveBalance.total), 0),
                func.coalesce(func.sum(LeaveBalance.used), 0),
                func.coalesce(func.sum(LeaveBalance.remaining), 0),
                func.coalesce(func.avg(LeaveBalance.remaining), 0),
            )
            .one()
        )

        return {
            "employee_count": int(employee_count),
            "total_allocated": int(total_allocated),
            "total_used": int(total_used),
            "total_remaining": int(total_remaining),
            "avg_remaining": float(avg_remaining),
        }
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()


def get_employee_leave_details(employee_id: int):
    db = SessionLocal()

    try:
        row = (
            db.query(Employee, LeaveBalance)
            .outerjoin(LeaveBalance, LeaveBalance.employee_id == Employee.id)
            .filter(Employee.id == employee_id)
            .first()
        )

        if not row:
            return {"error": "Employee not found"}

        employee, leave_balance = row

        details = {
            "employee_id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "role": employee.role,
            "leave": {
                "total": 0,
                "used": 0,
                "remaining": 0,
            },
        }

        if leave_balance:
            details["leave"] = {
                "total": leave_balance.total,
                "used": leave_balance.used,
                "remaining": leave_balance.remaining,
            }

        return details
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()


def get_low_leave_alerts(threshold: int = 3):
    db = SessionLocal()

    try:
        rows = (
            db.query(Employee, LeaveBalance)
            .join(LeaveBalance, LeaveBalance.employee_id == Employee.id)
            .filter(LeaveBalance.remaining <= threshold)
            .order_by(LeaveBalance.remaining.asc(), LeaveBalance.used.desc())
            .all()
        )

        alerts = [
            {
                "employee_id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "remaining": leave_balance.remaining,
                "used": leave_balance.used,
                "total": leave_balance.total,
            }
            for employee, leave_balance in rows
        ]

        return {
            "threshold": threshold,
            "count": len(alerts),
            "alerts": alerts,
        }
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()


def get_leave_leaderboard(limit: int = 5):
    db = SessionLocal()

    try:
        rows = (
            db.query(Employee, LeaveBalance)
            .join(LeaveBalance, LeaveBalance.employee_id == Employee.id)
            .order_by(LeaveBalance.used.desc(), LeaveBalance.remaining.asc())
            .limit(limit)
            .all()
        )

        leaderboard = [
            {
                "employee_id": employee.id,
                "name": employee.name,
                "email": employee.email,
                "used": leave_balance.used,
                "remaining": leave_balance.remaining,
                "total": leave_balance.total,
            }
            for employee, leave_balance in rows
        ]

        return {
            "limit": limit,
            "count": len(leaderboard),
            "leaders": leaderboard,
        }
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()


def list_employees(limit: int = 20):
    db = SessionLocal()

    try:
        rows = db.query(Employee).order_by(Employee.id.asc()).limit(limit).all()
        items = [
            {
                "employee_id": row.id,
                "name": row.name,
                "email": row.email,
                "role": row.role,
            }
            for row in rows
        ]
        return {"count": len(items), "employees": items}
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()


def search_employees(query: str, limit: int = 20):
    db = SessionLocal()

    try:
        q = f"%{query}%"
        rows = (
            db.query(Employee)
            .filter((Employee.name.ilike(q)) | (Employee.email.ilike(q)))
            .order_by(Employee.id.asc())
            .limit(limit)
            .all()
        )

        items = [
            {
                "employee_id": row.id,
                "name": row.name,
                "email": row.email,
                "role": row.role,
            }
            for row in rows
        ]
        return {"query": query, "count": len(items), "employees": items}
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()


def get_role_breakdown():
    db = SessionLocal()

    try:
        rows = (
            db.query(Employee.role, func.count(Employee.id))
            .group_by(Employee.role)
            .order_by(Employee.role.asc())
            .all()
        )

        breakdown = [{"role": role, "count": int(count)} for role, count in rows]
        total = sum(item["count"] for item in breakdown)
        return {"total_employees": total, "roles": breakdown}
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()


def get_manager_leave_dashboard(alert_threshold: int = 3, leaderboard_limit: int = 5):
    db = SessionLocal()

    try:
        employee_count, total_allocated, total_used, total_remaining, avg_remaining = (
            db.query(
                func.count(LeaveBalance.employee_id),
                func.coalesce(func.sum(LeaveBalance.total), 0),
                func.coalesce(func.sum(LeaveBalance.used), 0),
                func.coalesce(func.sum(LeaveBalance.remaining), 0),
                func.coalesce(func.avg(LeaveBalance.remaining), 0),
            )
            .one()
        )

        alert_rows = (
            db.query(Employee, LeaveBalance)
            .join(LeaveBalance, LeaveBalance.employee_id == Employee.id)
            .filter(LeaveBalance.remaining <= alert_threshold)
            .order_by(LeaveBalance.remaining.asc(), LeaveBalance.used.desc())
            .all()
        )
        alerts = [
            {
                "employee_id": employee.id,
                "name": employee.name,
                "remaining": leave_balance.remaining,
                "used": leave_balance.used,
            }
            for employee, leave_balance in alert_rows
        ]

        leaderboard_rows = (
            db.query(Employee, LeaveBalance)
            .join(LeaveBalance, LeaveBalance.employee_id == Employee.id)
            .order_by(LeaveBalance.used.desc(), LeaveBalance.remaining.asc())
            .limit(leaderboard_limit)
            .all()
        )
        leaders = [
            {
                "employee_id": employee.id,
                "name": employee.name,
                "used": leave_balance.used,
                "remaining": leave_balance.remaining,
            }
            for employee, leave_balance in leaderboard_rows
        ]

        return {
            "summary": {
                "employee_count": int(employee_count),
                "total_allocated": int(total_allocated),
                "total_used": int(total_used),
                "total_remaining": int(total_remaining),
                "avg_remaining": float(avg_remaining),
            },
            "alert_threshold": alert_threshold,
            "alerts_count": len(alerts),
            "alerts": alerts,
            "leaderboard_limit": leaderboard_limit,
            "leaderboard_count": len(leaders),
            "leaderboard": leaders,
        }
    except SQLAlchemyError:
        return {"error": "Database unavailable"}
    finally:
        db.close()