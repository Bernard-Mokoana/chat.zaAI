from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from backend.database.models.conversations import Conversation
from backend.database.models.messages import Message

async def save_chat_message(db: AsyncSession, user_id: str, chat_token: str, role: str, content: str):
    try:
        user_id_uuid = UUID(user_id)
        chat_token_uuid = UUID(chat_token)
    except ValueError as e:
        raise ValueError(f"Invalid UUID format: {e}")
    
    result = await db.execute(select(Conversation).filter(Conversation.id == chat_token_uuid))
    conversation  = result.scalars().first()

    if not conversation:
        conversation = Conversation(
            id=UUID(chat_token_uuid),
            user_id=user_id_uuid,
            title=(content[:50] if content else "New Chat") if role == "human" else "New Chat"
        )
        db.add(conversation)
        await db.flush()
    
    new_message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content,
    )
    db.add(new_message)
    await db.commit()

