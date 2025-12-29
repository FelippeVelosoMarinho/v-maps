# Routers package
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.maps import router as maps_router
from app.routers.places import router as places_router
from app.routers.check_ins import router as check_ins_router
from app.routers.chat import router as chat_router

__all__ = [
    "auth_router",
    "users_router",
    "maps_router",
    "places_router",
    "check_ins_router",
    "chat_router",
]
