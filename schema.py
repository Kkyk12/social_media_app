from pydantic import BaseModel
from pydantic.networks import EmailStr
from datetime import datetime
from typing import List


class TextInput(BaseModel):
    text: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str | None = None


class PostBase(BaseModel):
    content: str


class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: int
    post_id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PostWithStats(PostBase):
    id: int
    owner_id: int
    owner_email: EmailStr
    created_at: datetime
    likes_count: int
    comments_count: int
    comments: List[CommentResponse]

    class Config:
        from_attributes = True


class LikeResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserBasic(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    user: UserBasic
    followers_count: int
    following_count: int
    followers: List[UserBasic]
    following: List[UserBasic]

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    sender_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    message: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True