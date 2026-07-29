from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import router as api_v1_router
from app.api.v1.endpoints.root import router as root_router
from app.core.config import get_settings
from app.core.lifespan import lifespan

settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

if settings.app_env == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.trusted_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts,
    )

app.include_router(root_router)
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
