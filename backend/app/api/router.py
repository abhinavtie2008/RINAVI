from fastapi import APIRouter

from app.api.routes import health
from app.modules.applications import routes as applications
from app.modules.catalog import routes as catalog
from app.modules.consent import routes as consent
from app.modules.identity import routes as identity
from app.modules.locker import routes as locker
from app.modules.profile import routes as profile
from app.modules.vault import routes as vault

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(identity.router)
api_router.include_router(consent.router)
api_router.include_router(applications.router)
api_router.include_router(locker.router)
api_router.include_router(catalog.router)
api_router.include_router(vault.router)
api_router.include_router(profile.router)
