"""
agents/schedule_agent.py

Multi-Agent Engine for Predictive Schedule Risk.
Synthesizes signals from Procurement, Weather, and Workforce.
"""

import logging
from sqlalchemy.orm import Session
import models
import database
from llm_router import call_llm, TaskType

logger = logging.getLogger(__name__)

def analyze_schedule_risk() -> dict:
    """
    Coordinator agent: evaluates all critical path tasks.
    """
    db: Session = database.SessionLocal()
    try:
        tasks = db.query(models.ScheduleTask).filter(models.ScheduleTask.is_critical == True).all()
        
        results = []
        for task in tasks:
            # 1. Procurement Risk (Check linked equipment delays)
            # Find equipment linked to this task
            equip_list = db.query(models.Equipment).filter(models.Equipment.linked_task_id == task.task_id).all()
            procurement_delay = 0
            for eq in equip_list:
                for po in eq.purchase_orders:
                    for shp in po.shipments:
                        if shp.delay_estimate_days > procurement_delay:
                            procurement_delay = shp.delay_estimate_days

            # 2. Weather Risk (Mock for outdoor tasks)
            weather_risk = 0
            if "Concrete" in task.task_name or "Roof" in task.task_name:
                weather_risk = 3 # 3 days delay due to rain

            total_delay = max(procurement_delay, weather_risk)
            
            if total_delay > 0:
                driver = "Procurement Risk" if procurement_delay >= weather_risk else "Weather Risk"
                
                # 3. Coordinator Agent: Generate Mitigations
                prompt = f"""You are a Construction Schedule Coordinator.
                Task: {task.task_name}
                Delay Driver: {driver} ({total_delay} days)
                
                Provide 2 actionable mitigation options to recover the schedule.
                Output strictly in JSON format:
                {{"mitigations": ["Option 1", "Option 2"]}}
                """
                
                try:
                    llm_resp = call_llm(TaskType.REASONING, prompt)
                    import json
                    if "```json" in llm_resp:
                        json_str = llm_resp.split("```json")[1].split("```")[0].strip()
                    else:
                        json_str = llm_resp.strip()
                    data = json.loads(json_str)
                    
                    task.risk_driver = driver
                    task.risk_impact = f"+{total_delay} Days"
                    task.risk_score = float(total_delay)
                    task.mitigations = data.get("mitigations", [])
                    
                    results.append({"task": task.task_name, "driver": driver, "mitigations": task.mitigations})
                except Exception as e:
                    logger.error(f"Coordinator LLM parsing failed: {e}")

        db.commit()
        return {"status": "success", "risks_found": len(results), "details": results}

    except Exception as e:
        db.rollback()
        logger.error(f"Schedule agent error: {e}")
        return {"error": str(e)}
    finally:
        db.close()
