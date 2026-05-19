from fastapi import FastAPI
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistem Syntri")

@app.get("/")
def root():
    return {"message": "Sistem Syntri API"}