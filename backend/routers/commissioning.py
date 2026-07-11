from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import models
import database
from agents.commissioning_agent import evaluate_test_record

router = APIRouter(prefix="/commissioning", tags=["Commissioning"])

@router.get("/tests")
def list_tests(db: Session = Depends(database.get_db)):
    tests = db.query(models.TestProcedure).all()
    result = []
    for t in tests:
        # get latest record
        record = db.query(models.TestRecord).filter(models.TestRecord.procedure_id == t.id).order_by(models.TestRecord.created_at.desc()).first()
        status = record.status if record else "Pending"
        progress = record.progress if record else 0.0
        
        result.append({
            "id": t.procedure_number,
            "system": t.system_name,
            "status": status,
            "progress": progress,
            "failedPoints": len([r for r in record.results if not r.get("pass", True)]) if record else 0,
            "totalPoints": len(t.steps),
            "lastUpdated": record.updated_at.isoformat() if record and record.updated_at else "Never",
            "record_id": record.id if record else None
        })
    return result

@router.post("/evaluate/{record_id}")
def run_evaluation(record_id: int):
    res = evaluate_test_record(record_id)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res
