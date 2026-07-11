import database
import models
from sqlalchemy.orm import Session
from agents.simulator_agent import generate_world_simulation

def seed_db():
    database.Base.metadata.create_all(bind=database.engine)
    
    print("Generating dynamic world simulation using Gemini...")
    res = generate_world_simulation()
    
    if "error" in res:
        print(f"Error during simulation: {res['error']}")
    else:
        print("Dynamic database seeded successfully.")

if __name__ == "__main__":
    seed_db()
