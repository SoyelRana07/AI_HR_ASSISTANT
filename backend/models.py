from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from datetime import datetime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    role = Column(String)
    manager_id = Column(Integer, nullable=True)
    password_hash = Column(String, nullable=True)

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


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String)  # pending, approved, rejected
    reason = Column(String)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    employee_id = Column(Integer, index=True, nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
