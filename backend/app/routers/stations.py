from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, database

router = APIRouter(prefix="/stations", tags=["stations"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[dict])
def get_all_stations(db: Session = Depends(get_db)):
    stations = db.query(models.Station).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "frequency": s.frequency,
            "country": s.country,
            "type": s.type,
            "latitude": s.latitude,
            "longitude": s.longitude
        } for s in stations
    ]