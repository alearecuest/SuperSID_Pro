from fastapi import FastAPI
from . import models
from .database import engine
from .routers import users, observatories, stations

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SuperSID Pro Backend API")

app.include_router(users.router)
app.include_router(observatories.router)
app.include_router(stations.router)

@app.get("/")
def read_root():
    return {"message": "SuperSID Pro API is running!"}
