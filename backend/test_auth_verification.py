import sys
from backend.auth import authenticate_user

print("Testing Employee login (ID: 1, Pass: 0001)...")
emp = authenticate_user(1, "0001")
if emp:
    print(f"SUCCESS: Authenticated {emp.name} ({emp.role}) with hashed password!")
else:
    print("FAILED: Employee authentication failed")

print("Testing invalid password (ID: 1, Pass: wrong)...")
emp_wrong = authenticate_user(1, "wrong")
if not emp_wrong:
    print("SUCCESS: Incorrect password rejected as expected!")
else:
    print("FAILED: Wrong password allowed!")

print("Testing Manager login (ID: 2, Pass: 0002)...")
mgr = authenticate_user(2, "0002")
if mgr:
    print(f"SUCCESS: Authenticated {mgr.name} ({mgr.role}) with hashed password!")
else:
    print("FAILED: Manager authentication failed")
