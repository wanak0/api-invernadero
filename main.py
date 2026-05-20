from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, String, TIMESTAMP,text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List

import os

DATABASE_URL=os.getenv('DATABASE_URL','mysql+pymysql://api_user:password123@localhost/invernadero_db')

engine=create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LecturaDB(Base):
    __tablename__="lecturas"
    id = Column(Integer, primary_key=True, index=True)
    fecha_hora=Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    luz_valor=Column(Float)
    luz_estado=Column(String(20))
    temp_aire=Column(Float)
    hum_aire=Column(Float)
    extractor_estado=Column(String(20))
    hum_suelo=Column(Float)
    riego_estado=Column(String(20))

Base.metadata.create_all(bind=engine)

class LecturaCreate(BaseModel):
    luz_valor: float
    luz_estado: str
    temp_aire: float
    hum_aire: float
    extractor_estado: str
    hum_suelo: float
    riego_estado: str

class LecturaResponse(LecturaCreate):
    id: int
    fecha_hora:datetime

    class Config:
        from_attributes = True

app=FastAPI(title="API invernadero esp32")

app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],#esto hay que cambiarlo a la url del front
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/lecturas", response_model=LecturaResponse)
def crear_lectura(lectura: LecturaCreate, db: Session = Depends(get_db)):
    """El ESP32 hará un POST aquí con los datos de los sensores"""
    db_lectura = LecturaDB(**lectura.model_dump())
    db.add(db_lectura)
    db.commit()
    db.refresh(db_lectura)
    return db_lectura

@app.get("/api/lecturas/actual", response_model=LecturaResponse)
def obtener_lectura_actual(db: Session = Depends(get_db)):
    """React hará un GET aquí para mostrar el estado actual en el Dashboard"""
    lectura = db.query(LecturaDB).order_by(LecturaDB.id.desc()).first()
    if lectura is None:
        raise HTTPException(status_code=404, detail="No hay datos registrados aún")
    return lectura

@app.get("/api/lecturas/historial")
def obtener_historial(horas: int = 4, db: Session = Depends(get_db)):
    tiempo_limite = datetime.now() - timedelta(hours=horas)
    
    historial = db.query(LecturaDB).filter(LecturaDB.fecha_hora >= tiempo_limite).all()
    
    return historial
