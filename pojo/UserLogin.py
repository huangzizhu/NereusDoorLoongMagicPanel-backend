from pydantic import BaseModel, ConfigDict


class UserLoginForm(BaseModel):
    account: str
    hashedPassword: str

    model_config = ConfigDict(
        str_strip_whitespace=True
    )