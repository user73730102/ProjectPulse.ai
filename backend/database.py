from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import os

# Read from env, with fallback for local dev. Use pg8000 driver.
# The URL must use postgresql+pg8000:// instead of just postgresql://
default_url = "postgresql+pg8000://pulse_user:pulse_password@localhost:5432/pulse_db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", default_url)
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)
# Note: In production we'd use connection pooling and async engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
