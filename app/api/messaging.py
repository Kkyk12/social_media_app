from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core import security
import model
from schema import ConversationResponse, MessageCreate, MessageResponse
from app.core import crypto_util
from app.core.rate_limiter import rate_limiter


router = APIRouter(
    prefix="/conversations",
    tags=["Messaging"],
)


def _normalize_user_pair(user1_id: int, user2_id: int) -> tuple[int, int]:
    # store user1_id < user2_id to respect unique constraint
    return (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)


@router.post("/{other_user_id}", response_model=ConversationResponse)
def get_or_create_conversation(
    other_user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    current_user_id = int(current_user.id)
    # limit new/open conversation attempts
    rate_limiter.check_rate_limit(
        identifier=str(current_user_id),
        endpoint="conversation",
        limit=30,
        window_seconds=60,
    )
    if other_user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create conversation with yourself",
        )

    other = db.query(model.user).filter(model.user.id == other_user_id).first()
    if not other:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # require mutual follow before allowing conversation
    follows_current_to_other = (
        db.query(model.Follow)
        .filter(
            model.Follow.follower_id == current_user_id,
            model.Follow.following_id == other_user_id,
        )
        .first()
    )
    follows_other_to_current = (
        db.query(model.Follow)
        .filter(
            model.Follow.follower_id == other_user_id,
            model.Follow.following_id == current_user_id,
        )
        .first()
    )
    if not (follows_current_to_other and follows_other_to_current):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Both users must follow each other to start a conversation",
        )

    user1_id, user2_id = _normalize_user_pair(current_user_id, other_user_id)

    conv = (
        db.query(model.Conversation)
        .filter(
            model.Conversation.user1_id == user1_id,
            model.Conversation.user2_id == user2_id,
        )
        .first()
    )

    if not conv:
        conv = model.Conversation(user1_id=user1_id, user2_id=user2_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    return conv


@router.get("/", response_model=List[ConversationResponse])
def list_my_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    current_user_id = int(current_user.id)

    conversations = (
        db.query(model.Conversation)
        .filter(
            (model.Conversation.user1_id == current_user_id)
            | (model.Conversation.user2_id == current_user_id)
        )
        .order_by(model.Conversation.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return conversations


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    current_user_id = int(current_user.id)

    conv = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if current_user_id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    messages = (
        db.query(model.Message)
        .filter(model.Message.conversation_id == conversation_id)
        .order_by(model.Message.created_at.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # decrypt content before returning
    result = []
    for m in messages:
        decrypted = crypto_util.decrypt_text(m.content)
        result.append(
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                sender_id=m.sender_id,
                content=decrypted if decrypted is not None else "[unreadable]",
                created_at=m.created_at,
            )
        )
    return result


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    current_user_id = int(current_user.id)

    conv = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if current_user_id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    encrypted_content = crypto_util.encrypt_text(message.content)
    new_message = model.Message(
        conversation_id=conversation_id,
        sender_id=current_user_id,
        content=encrypted_content,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # notification for the other user
    recipient_id = conv.user1_id if current_user_id == conv.user2_id else conv.user2_id
    notif = model.Notification(
        user_id=recipient_id,
        type="message",
        message=f"New message in conversation {conversation_id}",
    )
    db.add(notif)
    db.commit()

    # return decrypted content in response
    return MessageResponse(
        id=new_message.id,
        conversation_id=new_message.conversation_id,
        sender_id=new_message.sender_id,
        content=message.content,
        created_at=new_message.created_at,
    )


@router.get("/{conversation_id}/unread_count")
def get_unread_count(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    current_user_id = int(current_user.id)

    conv = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if current_user_id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    unread_count = (
        db.query(model.Message)
        .filter(
            model.Message.conversation_id == conversation_id,
            model.Message.sender_id != current_user_id,
            model.Message.is_read == False,
        )
        .count()
    )

    return {"unread_count": unread_count}


@router.post("/{conversation_id}/mark_read", status_code=status.HTTP_200_OK)
def mark_conversation_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(security.get_current_user),
):
    current_user_id = int(current_user.id)

    conv = db.query(model.Conversation).filter(model.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if current_user_id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    (
        db.query(model.Message)
        .filter(
            model.Message.conversation_id == conversation_id,
            model.Message.sender_id != current_user_id,
            model.Message.is_read == False,
        )
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return {"detail": "Messages marked as read"}


__all__ = ["router"]
