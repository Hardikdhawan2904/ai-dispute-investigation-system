import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from database.database import SessionLocal, init_db
from database.models import DisputeCase
from agents.identity_trust_agent import run_identity_trust_agent

def verify():
    # Make sure DB has tables and columns
    init_db()
    
    db = SessionLocal()
    try:
        # Check if we have any cases
        case = db.query(DisputeCase).first()
        if not case:
            print("No cases in DB, creating a mock case...")
            case = DisputeCase(
                case_id="CASE_TEST_999",
                customer_id="CUST_001",
                customer_name="John Doe",
                email="john.doe@example.com",
                phone="+91-9876543210",
                transaction_id="TXN_999",
                transaction_type="UPI",
                merchant="Amazon",
                amount=15000.0,
                currency="INR",
                transaction_date="2026-06-11",
                transaction_time="12:00:00",
                dispute_reason="Unauthorized Transaction",
                fraud_selected=True,
                status="Dispute Raised",
                priority="HIGH",
                confidence_score=0.8,
                priority_score=80.0,
                requires_manual_review=False
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            print(f"Created case {case.case_id}")
        else:
            print(f"Using existing case {case.case_id}")
            
        # Run trust agent
        print("Running run_identity_trust_agent...")
        res = run_identity_trust_agent({}, case_id=case.case_id)
        
        print("\n--- AGENT 4 OUTPUT ---")
        import json
        print(json.dumps(res, indent=2))
        
        # Manually verify intermediate database saving
        # Since run_identity_trust_agent doesn't directly write to DB (that is handled in the workflow node),
        # let's simulate the workflow node's DB save helper to make sure writing works:
        from workflows.dispute_workflow import _save_identity_trust_to_db
        print("\nSimulating workflow DB save...")
        _save_identity_trust_to_db(case.case_id, res)
        
        db.refresh(case)
        print("\n--- DB UPDATES AFTER INTEGRATION ---")
        print(f"User Trust Score: {case.user_trust_score}")
        print(f"Behavioral Risk Score: {case.behavioral_risk_score}")
        print(f"Identity Status: {case.identity_status}")
        print(f"Trust Intel keys: {list(case.trust_intelligence.keys()) if case.trust_intelligence else None}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify()
