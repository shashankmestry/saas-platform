from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.shared.email import normalize_email


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_auth_user_id(self, auth_user_id: UUID) -> User | None:
        statement = select(User).where(User.auth_user_id == auth_user_id)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        normalized = normalize_email(email)
        statement = select(User).where(func.lower(func.trim(User.email)) == normalized)
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
