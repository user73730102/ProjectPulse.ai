"""
agents/supply_chain_agent.py

Evaluates shipments and identifies port congestion or transit delays.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import models
import database
from llm_router import call_llm, TaskType

logger = logging.getLogger(__name__)

def evaluate_shipment(shipment_id: int) -> dict:
    """
    Evaluate a shipment's location and status to detect delays.
    """
    db: Session = database.SessionLocal()
    try:
        shipment = db.query(models.Shipment).filter(models.Shipment.id == shipment_id).first()
        if not shipment:
            return {"error": "Shipment not found."}

        # Mocking external API carrier logic here with LLM logic
        # In a real app, we'd hit Maersk API.
        prompt = f"""You are a Supply Chain Risk Analyzer.
        Equipment: {shipment.purchase_order.equipment.name}
        Origin: {shipment.origin}
        Destination: {shipment.destination}
        Current Location: {shipment.current_location}
        Status: {shipment.status}

        Based on global supply chain knowledge, is there likely to be a delay?
        Output strictly in JSON format:
        {{"risk_flag": "Congestion/Customs/None", "delay_days": int}}
        """

        try:
            llm_resp = call_llm(TaskType.REASONING, prompt)
            import json
            # Extract JSON block
            if "```json" in llm_resp:
                json_str = llm_resp.split("```json")[1].split("```")[0].strip()
            else:
                json_str = llm_resp.strip()
            data = json.loads(json_str)

            if data.get("delay_days", 0) > 0:
                shipment.risk_flag = data.get("risk_flag", "Delay Detected")
                shipment.delay_estimate_days = data.get("delay_days", 0)
            else:
                shipment.risk_flag = None
                shipment.delay_estimate_days = 0

            db.commit()
            return {"status": "success", "risk_flag": shipment.risk_flag, "delay": shipment.delay_estimate_days}

        except Exception as e:
            logger.error(f"Failed to parse LLM response for supply chain: {e}")
            return {"error": str(e)}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
