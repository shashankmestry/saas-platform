"""Supabase Storage helpers for organization assets."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4

from supabase import AsyncClient, acreate_client

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

ALLOWED_LOGO_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)

_CONTENT_TYPE_EXTENSIONS: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

MAX_LOGO_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class SignedUploadAuthorization:
    bucket: str
    path: str
    token: str
    signed_url: str


@dataclass(frozen=True, slots=True)
class StoredObjectInfo:
    path: str
    content_type: str | None
    size: int | None


class StorageError(Exception):
    """Raised when a Storage operation fails."""


class OrganizationAssetsStorage:
    """Thin wrapper around Supabase Storage for organization logos."""

    def __init__(self, client: AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._bucket = settings.organization_assets_bucket

    @property
    def bucket(self) -> str:
        return self._bucket

    def build_logo_path(self, organization_id: UUID, content_type: str) -> str:
        extension = _CONTENT_TYPE_EXTENSIONS[content_type]
        filename = f"{uuid4().hex}.{extension}"
        return f"organizations/{organization_id}/logo/{filename}"

    def is_valid_logo_path_for_organization(
        self,
        organization_id: UUID,
        path: str,
    ) -> bool:
        expected_prefix = f"organizations/{organization_id}/logo/"
        if not path.startswith(expected_prefix):
            return False
        if ".." in path or path.startswith("/") or "//" in path:
            return False
        remainder = path[len(expected_prefix) :]
        if not remainder or "/" in remainder:
            return False
        name, _, extension = remainder.rpartition(".")
        if not name or extension.lower() not in {"jpg", "jpeg", "png", "webp"}:
            return False
        return name.isalnum() and all(char in "0123456789abcdef" for char in name.lower())

    async def create_signed_upload(
        self,
        path: str,
    ) -> SignedUploadAuthorization:
        try:
            result = await self._client.storage.from_(self._bucket).create_signed_upload_url(
                path,
            )
        except Exception as exc:
            logger.exception("Failed to create signed upload authorization")
            raise StorageError("Unable to create upload authorization") from exc

        token = result.get("token")
        signed_url = result.get("signed_url") or result.get("signedUrl")
        result_path = result.get("path") or path
        if not token or not signed_url:
            raise StorageError("Unable to create upload authorization")

        return SignedUploadAuthorization(
            bucket=self._bucket,
            path=result_path,
            token=token,
            signed_url=signed_url,
        )

    async def get_object_info(self, path: str) -> StoredObjectInfo | None:
        bucket = self._client.storage.from_(self._bucket)
        try:
            exists = await bucket.exists(path)
        except Exception as exc:
            logger.exception("Failed to check Storage object existence")
            raise StorageError("Unable to verify uploaded object") from exc

        if not exists:
            return None

        try:
            raw: dict[str, Any] = await bucket.info(path)
        except Exception as exc:
            logger.exception("Failed to read Storage object metadata")
            raise StorageError("Unable to verify uploaded object") from exc

        metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        content_type = (
            metadata.get("mimetype")
            or metadata.get("contentType")
            or raw.get("contentType")
            or raw.get("mimetype")
        )
        size_value = (
            metadata.get("size")
            or metadata.get("contentLength")
            or raw.get("size")
            or raw.get("contentLength")
        )
        size: int | None
        try:
            size = int(size_value) if size_value is not None else None
        except (TypeError, ValueError):
            size = None

        return StoredObjectInfo(
            path=path,
            content_type=str(content_type) if content_type else None,
            size=size,
        )

    async def create_signed_read_url(self, path: str) -> str | None:
        try:
            result = await self._client.storage.from_(self._bucket).create_signed_url(
                path,
                self._settings.logo_signed_url_ttl_seconds,
            )
        except Exception:
            logger.exception("Failed to create signed read URL for organization logo")
            return None

        signed_url = None
        if isinstance(result, dict):
            signed_url = result.get("signedURL") or result.get("signedUrl") or result.get(
                "signed_url"
            )
        return signed_url if isinstance(signed_url, str) and signed_url else None

    async def delete_object(self, path: str) -> None:
        try:
            await self._client.storage.from_(self._bucket).remove([path])
        except Exception as exc:
            logger.exception("Failed to delete Storage object path=%s", path.split("/")[-1])
            raise StorageError("Unable to delete storage object") from exc


_storage_client: AsyncClient | None = None


async def get_supabase_admin_client(settings: Settings | None = None) -> AsyncClient:
    global _storage_client
    if _storage_client is not None:
        return _storage_client

    resolved = settings or get_settings()
    _storage_client = await acreate_client(
        resolved.supabase_url,
        resolved.supabase_secret_key,
    )
    return _storage_client


async def get_organization_assets_storage(
    settings: Settings | None = None,
) -> OrganizationAssetsStorage:
    resolved = settings or get_settings()
    client = await get_supabase_admin_client(resolved)
    return OrganizationAssetsStorage(client=client, settings=resolved)


@lru_cache
def get_allowed_logo_content_types() -> frozenset[str]:
    return ALLOWED_LOGO_CONTENT_TYPES
