from backend.db import SessionLocal, engine
from backend.models import Base, Employee, Leave, LeaveBalance


EMPLOYEES = [
    {"id": 1, "name": "Aarav Sharma", "email": "aarav@company.com", "role": "employee", "manager_id": 2},
    {"id": 2, "name": "Riya Mehta", "email": "riya@company.com", "role": "manager", "manager_id": None},
    {"id": 3, "name": "Karan Singh", "email": "karan@company.com", "role": "employee", "manager_id": 2},
    {"id": 4, "name": "Neha Verma", "email": "neha@company.com", "role": "employee", "manager_id": 2},
    {"id": 5, "name": "Ishaan Patel", "email": "ishaan@company.com", "role": "employee", "manager_id": 2},
]

LEAVE_BALANCES = [
    {"employee_id": 1, "total": 20, "used": 6, "remaining": 14},
    {"employee_id": 2, "total": 25, "used": 4, "remaining": 21},
    {"employee_id": 3, "total": 20, "used": 12, "remaining": 8},
    {"employee_id": 4, "total": 20, "used": 18, "remaining": 2},
    {"employee_id": 5, "total": 20, "used": 9, "remaining": 11},
]


# Keep the legacy leaves table in sync for endpoints that still use it.
LEAVES = [
    {"id": 1, "employee_id": 1, "total": 20, "used": 6, "remaining": 14},
    {"id": 2, "employee_id": 2, "total": 25, "used": 4, "remaining": 21},
    {"id": 3, "employee_id": 3, "total": 20, "used": 12, "remaining": 8},
    {"id": 4, "employee_id": 4, "total": 20, "used": 18, "remaining": 2},
    {"id": 5, "employee_id": 5, "total": 20, "used": 9, "remaining": 11},
]


def _upsert_employee(db, payload):
    row = db.query(Employee).filter(Employee.id == payload["id"]).first()
    if row is None:
        row = Employee(**payload)
        db.add(row)
    else:
        row.name = payload["name"]
        row.email = payload["email"]
        row.role = payload["role"]
        row.manager_id = payload.get("manager_id")


def _upsert_leave_balance(db, payload):
    row = db.query(LeaveBalance).filter(LeaveBalance.employee_id == payload["employee_id"]).first()
    if row is None:
        row = LeaveBalance(**payload)
        db.add(row)
    else:
        row.total = payload["total"]
        row.used = payload["used"]
        row.remaining = payload["remaining"]


def _upsert_leave(db, payload):
    row = db.query(Leave).filter(Leave.id == payload["id"]).first()
    if row is None:
        row = Leave(**payload)
        db.add(row)
    else:
        row.employee_id = payload["employee_id"]
        row.total = payload["total"]
        row.used = payload["used"]
        row.remaining = payload["remaining"]


def seed_dummy_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for employee in EMPLOYEES:
            _upsert_employee(db, employee)

        for leave_balance in LEAVE_BALANCES:
            _upsert_leave_balance(db, leave_balance)

        for leave in LEAVES:
            _upsert_leave(db, leave)

        db.commit()
        print("Dummy data seeded successfully.")
        print("Login examples:")
        print("- Employee: ID 1, password 0001")
        print("- Manager:  ID 2, password 0002")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_dummy_data()
