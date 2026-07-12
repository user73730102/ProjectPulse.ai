"""
agents/commissioning_agent.py

Evaluates test records against acceptance criteria.
If a test fails, automatically drafts a Non-Conformance Report (NCR).
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
import models
import database
from llm_router import call_llm, TaskType

logger = logging.getLogger(__name__)

def evaluate_test_record(test_record_id: int) -> dict:
    """
    Evaluate a test record against its procedure.
    If it fails, auto-draft an NCR.
    """
    db: Session = database.SessionLocal()
    try:
        record = db.query(models.TestRecord).filter(models.TestRecord.id == test_record_id).first()
        if not record:
            return {"error": "Test record not found."}
            
        procedure = record.procedure
        if not procedure:
            return {"error": "Test procedure not found."}

        # Check if any step failed
        failed_steps = [res for res in record.results if not res.get("pass", True)]
        
        if not failed_steps:
            record.status = "Passed"
            record.progress = 100.0
            db.commit()
            return {"status": "Passed", "ncr_id": None}

        record.status = "Failed"
        db.commit()

        # Map step_no to expected_value from procedure steps
        expected_values = {step.get("step_no"): step.get("expected_value") for step in procedure.steps}

        # Draft an NCR for the failed test
        deviation_desc = f"Test Procedure {procedure.procedure_number} failed.\n"
        required_val_str = ""
        submitted_val_str = ""
        
        for fs in failed_steps:
            step_no = fs.get('step_no')
            actual = fs.get('actual_value')
            expected = expected_values.get(step_no, "Unknown")
            
            deviation_desc += f"- Step {step_no}: Expected {expected}, Actual {actual}\n"
            required_val_str += f"Step {step_no}: {expected}\n"
            submitted_val_str += f"Step {step_no}: {actual}\n"

        # Ask LLM to determine severity and summarize
        prompt = f"""You are a QA Copilot analyzing a failed commissioning test.
        System: {procedure.system_name}
        Deviation: {deviation_desc}
        
        Provide a concise severity rating (Critical, Major, Minor) and a 1-sentence recommended mitigation.
        Output exactly like:
        Severity: [Rating]
        Mitigation: [Action]
        """
        
        llm_resp = call_llm(TaskType.REASONING, prompt)
        
        severity = "Minor"
        if "Critical" in llm_resp: severity = "Critical"
        elif "Major" in llm_resp: severity = "Major"

        # Create NCR
        new_ncr = models.NonConformanceReport(
            ncr_number=f"NCR-TST-{record.id}",
            test_record_id=record.id,
            required_value=required_val_str.strip(),
            submitted_value=submitted_val_str.strip(),
            deviation_description=f"{deviation_desc}\n\nAI Analysis: {llm_resp}",
            severity=severity,
            status=models.NCRStatus.draft,
            ai_confidence=0.95
        )
        db.add(new_ncr)
        db.commit()
        db.refresh(new_ncr)

        return {"status": "Failed", "ncr_id": new_ncr.id}

    except Exception as e:
        db.rollback()
        logger.error(f"Commissioning agent error: {e}")
        return {"error": str(e)}
    finally:
        db.close()
