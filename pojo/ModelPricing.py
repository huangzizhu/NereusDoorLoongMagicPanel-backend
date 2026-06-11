from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelPricingCreate(BaseModel):
    model: str = Field(..., min_length=1, max_length=100)
    inputPrice: float = Field(default=1.0, ge=0)
    cachedInputPrice: float = Field(default=0.1, ge=0)
    outputPrice: float = Field(default=3.0, ge=0)
    multiplier: float = Field(default=1.0, ge=0)
    credentialId: Optional[int] = Field(None, ge=1)


class ModelPricingUpdate(BaseModel):
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    inputPrice: Optional[float] = Field(None, ge=0)
    cachedInputPrice: Optional[float] = Field(None, ge=0)
    outputPrice: Optional[float] = Field(None, ge=0)
    multiplier: Optional[float] = Field(None, ge=0)
    credentialId: Optional[int] = Field(None, ge=1)
    isActive: Optional[int] = Field(None, ge=0, le=1)


class ModelPricingResponse(BaseModel):
    pricingId: int
    model: str
    inputPrice: float
    cachedInputPrice: float
    outputPrice: float
    multiplier: float
    credentialId: Optional[int] = None
    isActive: int = 1
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)
