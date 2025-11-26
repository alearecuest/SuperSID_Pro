from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/register", response_model=schemas.UserShow)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    db_observatory = db.query(models.Observatory).filter(models.Observatory.number == user.observatory.number).first()
    if db_observatory:
        obs_instance = db_observatory
    else:
        obs_instance = models.Observatory(
            number=user.observatory.number,
            latitude=user.observatory.latitude,
            longitude=user.observatory.longitude,
            email=user.observatory.email
        )
        db.add(obs_instance)
        db.commit()
        db.refresh(obs_instance)
    new_user = models.User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        observatory_id=obs_instance.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password.")
    return {"user_id": db_user.id, "email": db_user.email}