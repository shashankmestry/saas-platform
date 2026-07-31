from uuid import UUID

from app.modules.auth.schemas import AuthenticatedUser
from app.modules.users.exceptions import UserInactiveError
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def get_or_create_from_auth(
        self,
        authenticated_user: AuthenticatedUser,
    ) -> User:
        auth_user_id = UUID(authenticated_user.id)
        existing_user = await self._repository.get_by_auth_user_id(auth_user_id)
        if existing_user is not None:
            if not existing_user.is_active:
                raise UserInactiveError("Platform user is inactive")
            return existing_user

        user = User(
            auth_user_id=auth_user_id,
            email=authenticated_user.email,
            display_name=None,
            avatar_url=None,
        )
        return await self._repository.create(user)
