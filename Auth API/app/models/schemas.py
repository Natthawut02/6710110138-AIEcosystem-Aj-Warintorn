from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
