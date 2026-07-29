from fastapi import APIRouter

from app.core.config import get_settings
from app.shared.responses import RootResponse

router = APIRouter()


@router.get("/", response_model=RootResponse, summary="Root endpoint")
def read_root() -> RootResponse:
    settings = get_settings()

    return RootResponse(
        name=settings.app_name,
        version=settings.app_version,
        status="running",
    )
