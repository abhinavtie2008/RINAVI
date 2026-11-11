from fastapi import APIRouter

from app.api.routes import health
from app.modules.consent import routes as consent
from app.modules.identity import routes as identity

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router)
api_router.include_router(consent.router)
