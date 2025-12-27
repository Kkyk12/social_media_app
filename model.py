from database import Base
from sqlalchemy import Column, Integer, String, TIMESTAMP, text, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship


class TextData(Base):
    __tablename__ = "textdata"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)


class user(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    owner = relationship("user")
    comments = relationship("Comment", back_populates="post", cascade="all, delete")
    likes = relationship("Like", back_populates="post", cascade="all, delete")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    post = relationship("Post", back_populates="comments")
    owner = relationship("user")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    post = relationship("Post", back_populates="likes")
    user = relationship("user")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_user_like"),
    )


class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    following_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    follower = relationship("user", foreign_keys=[follower_id])
    following = relationship("user", foreign_keys=[following_id])

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follower_following"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user2_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    user1 = relationship("user", foreign_keys=[user1_id])
    user2 = relationship("user", foreign_keys=[user2_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete")

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_conversation_users"),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    is_read = Column(Boolean, nullable=False, server_default=text("false"))

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("user")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(String, nullable=False)  # e.g. follow, like, comment, message
    message = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    is_read = Column(Boolean, nullable=False, server_default=text("false"))

    user = relationship("user")