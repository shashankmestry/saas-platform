from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import AuthenticatedUser

router = APIRouter()


@router.get(
    "/me",
    response_model=AuthenticatedUser,
    summary="Get the authenticated identity",
)
async def read_current_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    return current_user
