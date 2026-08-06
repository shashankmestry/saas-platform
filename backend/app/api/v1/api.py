from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.memberships.router import (
    invitations_router,
    organization_memberships_router,
)
from app.modules.organizations.router import router as organizations_router
from app.modules.plans.router import router as organization_plans_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(
    organizations_router,
    prefix="/organizations",
    tags=["organizations"],
)
router.include_router(
    organization_plans_router,
    prefix="/organizations",
    tags=["organizations"],
)
router.include_router(
    organization_memberships_router,
    prefix="/organizations",
    tags=["organizations"],
)
router.include_router(
    invitations_router,
    prefix="/invitations",
    tags=["invitations"],
)
