from sqlalchemy.orm import Session

from backend.server.src.services.conversation_services import ConversationService

conversation_service = ConversationService()

def save_chat_message(db: Session, user_id: str, chat_token: str, role: str, content: str):
    return conversation_service.save_chat_message(
        db=db,
        user_id=user_id,
        chat_token=chat_token,
        role=role,
        content=content
    )
