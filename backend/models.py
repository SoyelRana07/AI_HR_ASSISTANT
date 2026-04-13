# backend/models.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    role = Column(String)
    manager_id = Column(Integer, nullable=True)

class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer)
    total = Column(Integer)
    used = Column(Integer)
    remaining = Column(Integer)
    
class LeaveBalance(Base):
    __tablename__ = "leave_balance"

    employee_id = Column(Integer, primary_key=True, index=True)
    total = Column(Integer)
    used = Column(Integer)
    remaining = Column(Integer)