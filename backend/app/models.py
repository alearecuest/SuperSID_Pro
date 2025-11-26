from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    frequency = Column(Float)
    country = Column(String)
    type = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)