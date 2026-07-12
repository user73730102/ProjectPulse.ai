"""
agents/simulator_agent.py

Uses Gemini to dynamically generate mock data for Phase 2 modules.
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import models
import database
from llm_router import call_llm, TaskType

logger = logging.getLogger(__name__)

def generate_world_simulation() -> dict:
    """
    Clears existing Phase 2 mock data and generates a new world state using Gemini.
    """
    db: Session = database.SessionLocal()
    try:
        # Clear existing simulated data
        db.query(models.NonConformanceReport).filter(models.NonConformanceReport.test_record_id.isnot(None)).delete()
        db.query(models.Shipment).delete()
        db.query(models.PurchaseOrder).delete()
        db.query(models.Equipment).delete()
        db.query(models.TestRecord).delete()
        db.query(models.TestProcedure).delete()
        db.query(models.ScheduleTask).delete()
        db.commit()

        prompt = """You are a Data Centre EPC Project Simulator.
        Generate a highly realistic mock scenario for a construction project.
        I need strictly valid JSON with this exact structure, with NO markdown formatting around it (just the raw JSON string):
        {
          "equipment": [
            { "tag": "GEN-01", "name": "2MW Cummins Generator" },
            { "tag": "SWG-01", "name": "Schneider MV Switchgear" }
          ],
          "shipments": [
            { "equipment_tag": "GEN-01", "origin": "USA", "destination": "Site", "location": "Port of Long Beach", "status": "Customs", "eta_days_from_now": 5 },
            { "equipment_tag": "SWG-01", "origin": "France", "destination": "Site", "location": "Suez Canal", "status": "In Transit", "eta_days_from_now": 14 }
          ],
          "schedule_tasks": [
            { "task_id": "A100", "name": "Install Generators", "start_days_from_now": 2, "duration_days": 5, "linked_equipment": "GEN-01" },
            { "task_id": "A101", "name": "Install Switchgear", "start_days_from_now": 7, "duration_days": 10, "linked_equipment": "SWG-01" },
            { "task_id": "A102", "name": "Pour Cooling Tower Foundation", "start_days_from_now": 1, "duration_days": 3, "linked_equipment": null }
          ],
          "test_procedures": [
            {
              "number": "TST-01", "system": "UPS Integrated Test", "desc": "Load bank testing",
              "steps": [ {"step": 1, "desc": "Check input", "expected": "400V"} ]
            }
          ],
          "test_records": [
            {
              "procedure_number": "TST-01", "progress": 100, "status": "Pending",
              "results": [ {"step": 1, "actual": "390V", "pass": false} ]
            }
          ]
        }
        
        Generate exactly 3 pieces of equipment, 3 shipments, 3 schedule tasks, and 3 test procedures/records. Make the equipment and tasks highly specific to Data Centre construction (e.g., CRAC units, chillers, fiber routing, PDU installation). Ensure at least one test record fails.
        """

        llm_resp = call_llm(TaskType.REASONING, prompt)
        
        # Parse JSON
        text = llm_resp.strip()
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        data = json.loads(text.strip())
        
        # Inject the parsed data
        inject_world_data(db, data)
        
        return {"status": "success", "message": "World simulation generated successfully."}

    except Exception as e:
        db.rollback()
        logger.error(f"Simulator agent error: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def inject_world_data(db: Session, data: dict):
    """
    Injects specific mock data into the database. Assumes existing mock data is already cleared if needed.
    """
    now = datetime.now(timezone.utc)
    
    # 1. Equipment & POs
    eq_map = {}
    for eq_data in data.get("equipment", []):
        eq = models.Equipment(
            equipment_tag=eq_data.get("tag", "UKN"),
            name=eq_data.get("name", "Unknown Equipment")
        )
        db.add(eq)
        db.commit()
        db.refresh(eq)
        eq_map[eq_data.get("tag", "UKN")] = eq.id
        
        # Auto-generate a Purchase Order
        po = models.PurchaseOrder(
            po_number=f"PO-{eq.id}-2026",
            equipment_id=eq.id,
            vendor_name=f"Vendor for {eq.name}"
        )
        db.add(po)
        db.commit()
        db.refresh(po)
        
        # Find shipments for this equipment
        for shp_data in data.get("shipments", []):
            if shp_data.get("equipment_tag") == eq_data.get("tag"):
                shp = models.Shipment(
                    tracking_number=f"TRK-{po.id}-{shp_data.get('eta_days_from_now', 0)}",
                    purchase_order_id=po.id,
                    origin=shp_data.get("origin", "Unknown"),
                    destination=shp_data.get("destination", "Site"),
                    current_location=shp_data.get("location", "Unknown"),
                    status=shp_data.get("status", "Pending"),
                    eta=now + timedelta(days=int(shp_data.get("eta_days_from_now", 0)))
                )
                db.add(shp)
    
    # 2. Schedule Tasks
    for t_data in data.get("schedule_tasks", []):
        task = models.ScheduleTask(
            task_id=t_data.get("task_id", "T00"),
            task_name=t_data.get("name", "Unknown Task"),
            start_date=now + timedelta(days=int(t_data.get("start_days_from_now", 0))),
            end_date=now + timedelta(days=int(t_data.get("start_days_from_now", 0)) + int(t_data.get("duration_days", 1))),
            is_critical=True
        )
        db.add(task)
        db.commit()
        
        if t_data.get("linked_equipment") and t_data["linked_equipment"] in eq_map:
            eq = db.query(models.Equipment).filter(models.Equipment.id == eq_map[t_data["linked_equipment"]]).first()
            if eq:
                eq.linked_task_id = task.task_id
                db.commit()

    # 3. Commissioning
    for proc_data in data.get("test_procedures", []):
        proc = models.TestProcedure(
            procedure_number=proc_data.get("number", "P00"),
            system_name=proc_data.get("system", "General"),
            description=proc_data.get("desc", ""),
            steps=[{"step_no": s.get("step", 1), "description": s.get("desc", ""), "expected_value": s.get("expected", "")} for s in proc_data.get("steps", [])]
        )
        db.add(proc)
        db.commit()
        db.refresh(proc)
        
        # Find record for this procedure
        for rec_data in data.get("test_records", []):
            if rec_data.get("procedure_number") == proc_data.get("number"):
                rec = models.TestRecord(
                    procedure_id=proc.id,
                    results=[{"step_no": r.get("step", 1), "actual_value": r.get("actual", "0"), "pass": r.get("pass", True)} for r in rec_data.get("results", [])],
                    progress=rec_data.get("progress", 100),
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)
                
                # Automatically evaluate the simulated test record to generate an NCR if it failed
                from agents.commissioning_agent import evaluate_test_record
                evaluate_test_record(rec.id)
