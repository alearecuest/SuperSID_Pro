from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, database

router = APIRouter(prefix="/stations", tags=["stations"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.StationShow])
def get_all_stations(
    type: Optional[str] = Query(default=None, description="Filter by type"),
    country: Optional[str] = Query(default=None, description="Filter by country"),
    name: Optional[str] = Query(default=None, description="Filter by name"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Station)
    if type:
        query = query.filter(models.Station.type == type)
    if country:
        query = query.filter(models.Station.country.ilike(f"%{country}%"))
    if name:
        query = query.filter(models.Station.name.ilike(f"%{name}%"))
    return query.all()