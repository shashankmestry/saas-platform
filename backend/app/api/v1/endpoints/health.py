from fastapi import APIRouter

from app.shared.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
def healthcheck() -> HealthResponse:
    return HealthResponse(status="healthy")
