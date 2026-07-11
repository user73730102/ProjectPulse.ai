import database
from sqlalchemy import text

db = database.SessionLocal()
try:
    # Make existing foreign keys nullable
    db.execute(text("ALTER TABLE ncrs ALTER COLUMN submittal_id DROP NOT NULL;"))
    db.execute(text("ALTER TABLE ncrs ALTER COLUMN clause_id DROP NOT NULL;"))
    # Add new column if it doesn't exist
    db.execute(text("ALTER TABLE ncrs ADD COLUMN IF NOT EXISTS test_record_id INTEGER REFERENCES test_records(id);"))
    db.commit()
    print("Altered ncrs table successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
