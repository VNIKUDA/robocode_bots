from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, pool_size=30, max_overflow=0
)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()

days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

from database import models

def resetDatabase():
    models.Base.metadata.drop_all(bind=engine)

def setupDatabase():
    models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
