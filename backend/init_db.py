"""
init_db.py — Run this once to create all tables and enable pgvector extension.

Usage:
    python init_db.py

Safe to run multiple times (uses CREATE TABLE IF NOT EXISTS via SQLAlchemy).
"""

import time
import logging
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from database import engine, Base
import models  # noqa: F401 — importing models registers them with Base.metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init():
    print("Waiting for database...")
    max_retries = 10
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established.")
            break
        except OperationalError:
            if i < max_retries - 1:
                logger.warning(f"Database not ready. Retrying in 2 seconds ({i+1}/{max_retries})...")
                time.sleep(2)
            else:
                logger.error("Could not connect to the database after multiple retries.")
                raise

    print("Enabling pgvector extension...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialised successfully.")

if __name__ == "__main__":
    init()
