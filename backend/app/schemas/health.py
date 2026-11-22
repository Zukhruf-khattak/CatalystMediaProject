from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["healthy"]
    app_name: str
    version: str
    environment: str


class ReadyResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ready", "degraded"]
    database: bool
    app_name: str
    version: str
    environment: str
