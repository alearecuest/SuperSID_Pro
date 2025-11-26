from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(prefix="/observatories", tags=["observatories"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ObservatoryShow)
def create_observatory(observatory: schemas.ObservatoryCreate, db: Session = Depends(get_db)):
    db_obs = db.query(models.Observatory).filter(models.Observatory.number == observatory.number).first()
    if db_obs:
        raise HTTPException(status_code=400, detail="Observatory number already registered.")
    new_obs = models.Observatory(
        number=observatory.number,
        latitude=observatory.latitude,
        longitude=observatory.longitude,
        email=observatory.email
    )
    db.add(new_obs)
    db.commit()
    db.refresh(new_obs)
    return new_obs

@router.get("/{obs_id}", response_model=schemas.ObservatoryShow)
def get_observatory(obs_id: int, db: Session = Depends(get_db)):
    obs = db.query(models.Observatory).filter(models.Observatory.id == obs_id).first()
    if not obs:
        raise HTTPException(status_code=404, detail="Observatory not found")
    return obs