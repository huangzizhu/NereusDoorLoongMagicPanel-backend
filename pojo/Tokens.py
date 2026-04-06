from pydantic import BaseModel,Field

class Tokens(BaseModel):
    accessToken: str
    refreshToken: str = Field(...)