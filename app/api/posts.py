# Posts router re-export, so imports can use app.api.posts.router

from post import router  # type: ignore

__all__ = ["router"]
