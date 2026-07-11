from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import database
from agents.supply_chain_agent import evaluate_shipment

router = APIRouter(prefix="/supply-chain", tags=["Supply Chain"])

@router.get("/shipments")
def get_shipments(db: Session = Depends(database.get_db)):
    shipments = db.query(models.Shipment).all()
    result = []
    for s in shipments:
        result.append({
            "id": s.tracking_number,
            "equipment": s.purchase_order.equipment.name if s.purchase_order and s.purchase_order.equipment else "Unknown",
            "vendor": s.purchase_order.vendor_name if s.purchase_order else "Unknown",
            "origin": s.origin,
            "destination": s.destination,
            "status": s.status,
            "location": s.current_location,
            "eta": s.eta.strftime("%b %d, %Y") if s.eta else "Unknown",
            "riskFlag": s.risk_flag,
            "delayEstimate": f"+{s.delay_estimate_days} Days" if s.delay_estimate_days else None,
            "shipment_db_id": s.id
        })
    return result

@router.post("/evaluate/{shipment_id}")
def run_evaluation(shipment_id: int):
    res = evaluate_shipment(shipment_id)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return res
