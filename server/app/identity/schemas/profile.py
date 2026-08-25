from datetime import date
from typing import Optional

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    phone: str
    date_of_birth: date
    gender: str
    occupation: str
    marital_status: str
    country: str
    state: str
    city: str


class ProfileResponse(ProfileCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True