import random
from datetime import date, timedelta
from backend.db import SessionLocal, engine
from backend.models import Base, Employee, Leave, LeaveBalance, LeaveRequest
from backend.auth import hash_password

FIRST_NAMES = [
    "Aarav", "Riya", "Karan", "Neha", "Ishaan", "Priya", "Ananya", "Vikram",
    "Aditya", "Sneha", "Rahul", "Pooja", "Rohan", "Tanvi", "Siddharth", "Meera",
    "Kabir", "Shruti", "Dev", "Kavya", "Arjun", "Deepika", "Manish", "Divya",
    "Sanjay", "Nisha", "Amit", "Swati", "Rajesh", "Simran", "Varun", "Bhavna",
    "Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley"
]

LAST_NAMES = [
    "Sharma", "Mehta", "Singh", "Verma", "Patel", "Gupta", "Joshi", "Kumar",
    "Rao", "Nair", "Reddy", "Chawla", "Deshmukh", "Agarwal", "Bhat", "Kapoor",
    "Malhotra", "Saxena", "Choudhury", "Shah", "Smith", "Johnson", "Williams", "Brown"
]

DEPARTMENTS = ["Engineering", "Product", "Marketing", "HR", "Finance", "Operations", "Sales", "Legal"]

REASONS = [
    "Annual family vacation",
    "Personal wellness & health checkup",
    "Attending wedding ceremony",
    "Home renovation supervision",
    "Dental procedure recovery",
    "Child care & school event",
    "Relocation & moving house",
    "Festival celebration with family"
]


def generate_large_dataset(num_employees=500):
    print(f"Generating realistic enterprise dataset with {num_employees} employees...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    random.seed(42)  # Deterministic seed for reproducible testing

    try:
        employees = []
        leave_balances = []
        leaves = []
        leave_requests = []

        default_pwd_hash = hash_password("0000")

        # 1. Preset Core Test Accounts
        # Employee ID 1: Aarav Sharma (employee)
        employees.append(Employee(id=1, name="Aarav Sharma", email="aarav@company.com", role="employee", manager_id=2, password_hash=hash_password("0001")))
        leave_balances.append(LeaveBalance(employee_id=1, total=20, used=6, remaining=14))
        leaves.append(Leave(id=1, employee_id=1, total=20, used=6, remaining=14))

        # Manager ID 2: Riya Mehta (manager)
        employees.append(Employee(id=2, name="Riya Mehta", email="riya@company.com", role="manager", manager_id=None, password_hash=hash_password("0002")))
        leave_balances.append(LeaveBalance(employee_id=2, total=25, used=4, remaining=21))
        leaves.append(Leave(id=2, employee_id=2, total=25, used=4, remaining=21))

        # Select managers (every 25th employee is a manager)
        manager_ids = [2] + [i for i in range(10, num_employees + 1, 25)]

        # 2. Generate Remaining Employees
        for i in range(3, num_employees + 1):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}{i}@company.com"
            is_mgr = i in manager_ids
            role = "manager" if is_mgr else "employee"
            manager_id = None if is_mgr else random.choice(manager_ids)

            employees.append(Employee(id=i, name=name, email=email, role=role, manager_id=manager_id, password_hash=default_pwd_hash))

            total = random.choice([20, 22, 25, 30])
            used = random.randint(0, total)
            remaining = total - used

            leave_balances.append(LeaveBalance(employee_id=i, total=total, used=used, remaining=remaining))
            leaves.append(Leave(id=i, employee_id=i, total=total, used=used, remaining=remaining))

        # 3. Generate Leave Requests
        today = date.today()

        for emp_id in range(1, num_employees + 1):
            if random.random() < 0.35:  # 35% of employees have submitted leave requests
                num_reqs = random.randint(1, 3)
                for _ in range(num_reqs):
                    start_offset = random.randint(-30, 30)
                    duration = random.randint(1, 5)
                    start_date = today + timedelta(days=start_offset)
                    end_date = start_date + timedelta(days=duration)
                    status = random.choice(["pending", "approved", "rejected", "pending"])
                    reason = random.choice(REASONS)

                    leave_requests.append(LeaveRequest(
                        employee_id=emp_id,
                        start_date=start_date,
                        end_date=end_date,
                        status=status,
                        reason=reason
                    ))

        print("Bulk inserting records into PostgreSQL...")
        db.bulk_save_objects(employees)
        db.bulk_save_objects(leave_balances)
        db.bulk_save_objects(leaves)
        db.bulk_save_objects(leave_requests)

        db.commit()
        print(f"Successfully seeded {len(employees)} employees, {len(leave_balances)} leave balances, and {len(leave_requests)} leave requests!")
        print("\nTest Logins:")
        print("  - Employee 1: Aarav Sharma (pwd: 0001)")
        print("  - Manager 2:  Riya Mehta (pwd: 0002)")
        print("  - Default pwd for generated employees 3-500: 0000")
    except Exception as exc:
        db.rollback()
        print(f"Failed to seed large dataset: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    generate_large_dataset(500)
