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


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    employee_id = Column(Integer, index=True, nullable=True)
    role = Column(String, nullable=True)
    event_type = Column(String, nullable=False, index=True)  # TOOL_EXECUTION, SECURITY_REJECTION, PROMPT_INJECTION
    tool_name = Column(String, nullable=True)
    parameters = Column(Text, nullable=True)
    status = Column(String, nullable=False)  # SUCCESS, FAILED, REJECTED, FORBIDDEN
    execution_time_ms = Column(Integer, default=0)
    details = Column(Text, nullable=True)

