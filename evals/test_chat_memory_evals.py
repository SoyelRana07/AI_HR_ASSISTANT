import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.repository.chat_repo import save_chat_message, get_chat_history, clear_chat_history
from backend.db import SessionLocal, engine
from backend.models import Base


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_chat_memory_save_and_retrieve():
    session_id = "test_sess_001"
    employee_id = 999
    
    # Clean up prior test data
    clear_chat_history(session_id, employee_id)
    
    # Save user message
    msg1 = save_chat_message(session_id, employee_id, "user", "Hello HR Assistant!")
    assert msg1.id is not None
    assert msg1.sender == "user"
    
    # Save assistant response
    msg2 = save_chat_message(session_id, employee_id, "assistant", "Hello! How can I help you?")
    assert msg2.id is not None
    assert msg2.sender == "assistant"
    
    # Retrieve history
    history = get_chat_history(session_id, employee_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello HR Assistant!"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hello! How can I help you?"
    
    # Clean up
    deleted = clear_chat_history(session_id, employee_id)
    assert deleted == 2
    assert len(get_chat_history(session_id, employee_id)) == 0


def test_multi_turn_conversation_flow():
    """Test realistic 5-turn conversation history persistence and ordering."""
    session_id = "test_multi_turn_sess"
    employee_id = 1
    
    clear_chat_history(session_id, employee_id)
    
    turns = [
        ("user", "Show my leave balance"),
        ("assistant", "You have 14 remaining leave days out of 20 total."),
        ("user", "Can I take 3 days off next week?"),
        ("assistant", "Yes, you have enough balance remaining (14 days)."),
        ("user", "Submit a leave request for 2026-08-10 to 2026-08-12 for Vacation"),
        ("assistant", "Leave request submitted successfully for approval."),
    ]
    
    for sender, text in turns:
        save_chat_message(session_id, employee_id, sender, text)
        
    history = get_chat_history(session_id, employee_id)
    assert len(history) == 6
    assert history[0]["content"] == "Show my leave balance"
    assert history[5]["content"] == "Leave request submitted successfully for approval."
    
    clear_chat_history(session_id, employee_id)


def test_chat_history_limit_cap():
    """Verify that get_chat_history respects maximum message limit parameter."""
    session_id = "test_limit_sess"
    employee_id = 2
    
    clear_chat_history(session_id, employee_id)
    
    # Save 10 turns (20 messages)
    for i in range(10):
        save_chat_message(session_id, employee_id, "user", f"User question {i+1}")
        save_chat_message(session_id, employee_id, "assistant", f"Assistant answer {i+1}")
        
    # Request only top 4 messages
    limited_history = get_chat_history(session_id, employee_id, limit=4)
    assert len(limited_history) == 4
    
    clear_chat_history(session_id, employee_id)
