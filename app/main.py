from fastapi import FastAPI

from .core.db import engine
from .models import Base
from .api import auth, posts, follow_profile, messaging, notifications, users


# Create DB tables
Base.metadata.create_all(bind=engine)


tags_metadata = [
    {"name": "Users", "description": "User registration and basic user operations."},
    {"name": "Authentication", "description": "Login and logout."},
    {"name": "Posts", "description": "Create and manage posts, comments, and likes."},
    {"name": "Profile", "description": "User profiles and follower information."},
    {"name": "Follow", "description": "Follow and unfollow users."},
    {"name": "Messaging", "description": "1-to-1 conversations and messages."},
    {"name": "Notifications", "description": "User notifications for social actions."},
]


app = FastAPI(openapi_tags=tags_metadata)

# Include routers from the app.api package
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(follow_profile.router)
app.include_router(messaging.router)
app.include_router(notifications.router)
app.include_router(users.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
