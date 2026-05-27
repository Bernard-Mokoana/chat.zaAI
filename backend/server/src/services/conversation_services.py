from sqlalchemy.orm import Session
from sqlalchemy.future import select
from uuid import UUID

from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message

def save_chat_message(db: Session, user_id: str, chat_token: str, role: str, content: str):
    conversation = db.query(Conversation).filter(Conversation.id == chat_token).first()

    if not conversation:
        conversation = Conversation(
            id=UUID(chat_token),
            user_id=user_id,
            title=(content[:50] if content else "New Chat") if role == "human" else "New Chat"
        )
        db.add(conversation)
        db.flush()
    
    new_message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
    )
    db.add(new_message)
    db.commit()

