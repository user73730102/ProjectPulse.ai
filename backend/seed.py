import database
import models
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

def seed_db():
    database.Base.metadata.create_all(bind=database.engine)
    db: Session = database.SessionLocal()
    
    # 1. Seed Commissioning
    if db.query(models.TestProcedure).count() == 0:
        proc1 = models.TestProcedure(
            procedure_number="TST-001",
            system_name="UPS Integrated System",
            description="Full load bank and battery discharge test.",
            steps=[
                {"step_no": 1, "description": "Verify input voltage", "expected_value": "400V"},
                {"step_no": 2, "description": "Verify output voltage on battery", "expected_value": "400V"}
            ]
        )
        db.add(proc1)
        db.commit()

        rec1 = models.TestRecord(
            procedure_id=proc1.id,
            results=[
                {"step_no": 1, "actual_value": "398V", "pass": True},
                {"step_no": 2, "actual_value": "385V", "pass": False}
            ],
            progress=100.0,
            status="Pending" # Pending agent evaluation
        )
        db.add(rec1)

    # 2. Seed Schedule
    if db.query(models.ScheduleTask).count() == 0:
        now = datetime.now(timezone.utc)
        task1 = models.ScheduleTask(
            task_id="A1010",
            task_name="Foundation Concrete Pour (Zone B)",
            start_date=now + timedelta(days=2),
            end_date=now + timedelta(days=5),
            is_critical=True
        )
        task2 = models.ScheduleTask(
            task_id="A1020",
            task_name="Install Main Switchgear",
            start_date=now + timedelta(days=10),
            end_date=now + timedelta(days=15),
            is_critical=True
        )
        db.add_all([task1, task2])
        db.commit()

        # 3. Seed Equipment, PO, Shipment
        eq1 = models.Equipment(
            equipment_tag="SWG-01",
            name="Main Distribution Switchgear",
            linked_task_id="A1020"
        )
        db.add(eq1)
        db.commit()

        po1 = models.PurchaseOrder(
            po_number="PO-2026-001",
            equipment_id=eq1.id,
            vendor_name="Schneider Electric"
        )
        db.add(po1)
        db.commit()

        shp1 = models.Shipment(
            tracking_number="TRK-987654321",
            purchase_order_id=po1.id,
            origin="Grenoble, France",
            destination="Data Centre Site (Zone A)",
            current_location="Port of Singapore (Transshipment)",
            status="In Transit",
            eta=now + timedelta(days=20) # ETA is after task start date!
        )
        db.add(shp1)
        db.commit()

    db.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_db()
