from pydantic import BaseModel, EmailStr
from typing import Optional

class ObservatoryBase(BaseModel):
    number: int
    latitude: float
    longitude: float
    email: EmailStr

class ObservatoryCreate(ObservatoryBase):
    pass

class ObservatoryShow(ObservatoryBase):
    id: int

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    observatory: ObservatoryCreate

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserShow(BaseModel):
    id: int
    email: EmailStr
    observatory: ObservatoryShow

    class Config:
        from_attributes = True

class StationShow(BaseModel):
    id: int
    name: str
    frequency: Optional[float]
    country: str
    type: str
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True