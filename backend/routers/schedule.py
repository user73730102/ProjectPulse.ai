from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import database
from agents.schedule_agent import analyze_schedule_risk

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.get("/risks")
def get_schedule_risks(db: Session = Depends(database.get_db)):
    tasks = db.query(models.ScheduleTask).filter(models.ScheduleTask.is_critical == True).all()
    result = []
    for t in tasks:
        if t.risk_score > 0:
            result.append({
                "id": t.task_id,
                "task": t.task_name,
                "driver": t.risk_driver,
                "description": f"AI Risk Assessment: {t.risk_driver} delaying task by {t.risk_impact}",
                "impact": t.risk_impact,
                "severity": "Critical" if t.risk_score >= 5 else ("Major" if t.risk_score >= 3 else "Minor"),
                "mitigations": t.mitigations or []
            })
    return result

@router.post("/analyze")
def run_analysis():
    res = analyze_schedule_risk()
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res
