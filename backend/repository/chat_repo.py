from backend.db import SessionLocal
from backend.models import ChatMessage
from typing import List, Dict


def save_chat_message(session_id: str, employee_id: int, sender: str, content: str) -> ChatMessage:
    """Save a chat message (user or assistant) into the database."""
    db = SessionLocal()
    try:
        msg = ChatMessage(
            session_id=session_id,
            employee_id=employee_id,
            sender=sender,
            content=str(content),
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg
    finally:
        db.close()


def get_chat_history(session_id: str, employee_id: int, limit: int = 50) -> List[Dict[str, str]]:
    """Retrieve structured chat history for a given session and employee."""
    db = SessionLocal()
    try:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id, ChatMessage.employee_id == employee_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "role": msg.sender,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else "",
            }
            for msg in messages
        ]
    finally:
        db.close()


def clear_chat_history(session_id: str, employee_id: int) -> int:
    """Delete all messages for a session and employee."""
    db = SessionLocal()
    try:
        deleted_count = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id, ChatMessage.employee_id == employee_id)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted_count
    finally:
        db.close()
