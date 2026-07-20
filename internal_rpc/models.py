from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InternalRpcErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    PEER_UID_DENIED = "PEER_UID_DENIED"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"
    SIGNATURE_EXPIRED = "SIGNATURE_EXPIRED"
    NONCE_REPLAY = "NONCE_REPLAY"
    UNKNOWN_METHOD = "UNKNOWN_METHOD"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class InternalRpcCaller(BaseModel):
    source: str = Field(..., min_length=1, max_length=100)
    userId: int | None = None


class InternalRpcRequest(BaseModel):
    requestId: str = Field(..., min_length=1, max_length=100)
    method: str = Field(..., min_length=1, max_length=120)
    params: dict[str, Any] = Field(default_factory=dict)
    caller: InternalRpcCaller
    timestamp: str = Field(..., min_length=1)
    nonce: str = Field(..., min_length=8, max_length=128)
    signature: str = Field(..., min_length=1)


class InternalRpcResponse(BaseModel):
    success: bool
    auditId: str
    data: Any | None = None
    errorCode: str | None = None
    errorMessage: str | None = None
    errorDetails: str | None = None
