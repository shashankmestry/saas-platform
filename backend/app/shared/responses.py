from typing import Literal

from pydantic import BaseModel


class RootResponse(BaseModel):
    name: str
    version: str
    status: Literal["running"]


class HealthResponse(BaseModel):
    status: Literal["healthy"]
