import sys
import os
import random
import json
from datetime import datetime, timedelta, timezone

# Add backend directory to path
sys.path.append(r"d:\Transaction_dispute_agent\ai-dispute-resolution-system\backend")

from dotenv import load_dotenv
load_dotenv(r"d:\Transaction_dispute_agent\ai-dispute-resolution-system\backend\.env")

from database.database import SessionLocal, init_db
from database.models import (
    BankCustomer, MerchantProfile, Transaction, DisputeCase, 
    DocumentRequest, AuditLog, WorkflowState, DisputeHistory
)

# Categories and their details
CATEGORIES = [
    "Unauthorized Transaction",
    "Duplicate Transaction",
    "Refund Not Received",
    "Product Not Received",
    "Subscription Abuse",
    "ATM Cash Issue",
    "Merchant Dispute",
    "Friendly Fraud"
]

CATEGORY_REASONS = {
    "Unauthorized Transaction": ["Fraudulent transaction", "Card not present fraud", "Account taken over"],
    "Duplicate Transaction": ["Charged twice for same order", "Double debit", "Duplicate billing"],
    "Refund Not Received": ["Merchant promised refund but not received", "Returned product, no refund"],
    "Product Not Received": ["Paid but item never delivered", "Delivery delayed indefinitely"],
    "Subscription Abuse": ["Recurring charge after cancellation", "Unauthorised subscription renewal"],
    "ATM Cash Issue": ["ATM debited amount but cash not dispensed", "Partial cash dispensed"],
    "Merchant Dispute": ["Defective item received", "Incorrect billing amount by merchant"],
    "Friendly Fraud": ["Family member used card without permission", "Forgot making purchase"]
}

REQUIRED_DOCUMENTS = {
    "Unauthorized Transaction": [
        "Bank statement (last 3 months)",
        "SMS / email transaction alert screenshot",
        "OTP receipt (if applicable)",
        "Police FIR or written complaint (if filed)"
    ],
    "Duplicate Transaction": [
        "Bank statement showing both charges",
        "Transaction receipt or confirmation"
    ],
    "Refund Not Received": [
        "Original payment receipt",
        "Refund confirmation from merchant",
        "Bank statement (last 30 days)",
        "Merchant communication (email / chat screenshot)"
    ],
    "Product Not Received": [
        "Order confirmation or invoice",
        "Payment receipt",
        "Merchant communication",
        "Delivery tracking information"
    ],
    "Subscription Abuse": [
        "Subscription terms and conditions",
        "Cancellation confirmation (if obtained)",
        "Bank statement showing recurring charges"
    ],
    "ATM Cash Issue": [
        "ATM transaction receipt",
        "Bank statement showing debit",
        "Written complaint to branch (if filed)"
    ],
    "Merchant Dispute": [
        "Original invoice or receipt",
        "Merchant communication (email / chat / SMS)",
        "Photos of product or service (if relevant)"
    ],
    "Friendly Fraud": [
        "Original purchase receipt"
    ]
}

FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Aavya", "Ananya", "Diya", "Priya", "Riya", "Kavya", "Ira", "Sanya", "Rahul", "Amit", "Sanjay", "Vikram", "Sunita", "Deepak", "Rajesh", "Neha", "Pooja", "Anil", "Meera", "Vijay", "Anita", "Jyoti", "Rohan"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Mehta", "Joshi", "Patel", "Shah", "Reddy", "Nair", "Iyer", "Rao", "Singh", "Kumar", "Choudhary", "Das", "Sen", "Chatterjee", "Banerjee", "Mishra", "Pandey", "Dubey", "Yadav", "Prasad", "Naik", "Shetty", "Gowda", "Pillai", "Menon", "Bose", "Ghosh"]

MERCHANT_NAMES = {
    "Unauthorized Transaction": ["Apple Store", "Amazon Store", "Google Play Store", "Netflix US", "Microsoft", "PlayStation Network", "Steam Games", "Uber Trip Help"],
    "Duplicate Transaction": ["Zomato Food", "Swiggy Delivery", "Domino's Pizza", "BookMyShow Tickets", "Uber Eats", "Starbucks Coffee", "PVR Cinemas"],
    "Refund Not Received": ["Flipkart", "Myntra", "Meesho Seller", "Nykaa", "Ajio Fashion", "Tata Cliq", "Decathlon Sports"],
    "Product Not Received": ["Amazon Seller Portal", "Flipkart Online Retail", "Ebay Global Market", "Snapdeal Seller", "AliExpress Import"],
    "Subscription Abuse": ["Netflix Prime Monthly", "Spotify India Premium", "Amazon Prime Annual", "YouTube Premium Sub", "Adobe Creative Cloud", "Microsoft 365 Home"],
    "ATM Cash Issue": ["SBI ATM Branch 012", "HDFC Bank ATM Mumbai", "ICICI Bank ATM South", "Axis Bank ATM East", "PNB ATM Central"],
    "Merchant Dispute": ["Croma Electronics", "Reliance Digital Store", "Vijay Sales Mumbai", "Decathlon Retail", "Fabindia Clothing", "Zara Apparel"],
    "Friendly Fraud": ["Google Play Games", "App Store Billing", "Steam Games Billing", "PlayStation Network Store", "Roblox Purchase"]
}

def generate_random_customer(idx):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    full_name = f"{first} {last}"
    customer_id = f"CUST-{idx:06d}"
    email = f"{first.lower()}.{last.lower()}.{idx}@example.com"
    phone = f"+91{random.randint(6000000000, 9999999999)}"
    joining_date = datetime.now().date() - timedelta(days=random.randint(30, 1000))
    return BankCustomer(
        customer_id=customer_id,
        full_name=full_name,
        email=email,
        phone=phone,
        joining_date=joining_date
    )

def generate_random_merchant(idx):
    category = random.choice(CATEGORIES)
    templates = MERCHANT_NAMES.get(category, ["General Merchant", "Retail Mart", "Digital Shop", "Global Goods"])
    merchant_name = f"{random.choice(templates)} {random.randint(10, 99)}"
    merchant_id = f"MERCH-{idx:05d}"
    risk_level = random.choice(["LOW", "MEDIUM", "HIGH"])
    return MerchantProfile(
        merchant_id=merchant_id,
        merchant_name=merchant_name,
        merchant_category=category,
        total_transactions=random.randint(100, 10000),
        total_disputes=random.randint(0, 10),
        fraud_complaints=random.randint(0, 5),
        resolved_customer_favor=random.randint(0, 5),
        resolved_merchant_favor=random.randint(0, 5),
        risk_level=risk_level,
        blacklisted=False,
        created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(30, 500))
    )

def generate_random_dispute(case_idx, customers, merchants):
    customer = random.choice(customers)
    merchant = random.choice(merchants)
    category = random.choice(CATEGORIES)
    reason = random.choice(CATEGORY_REASONS[category])
    
    case_id = f"CASE-{case_idx:06d}"
    txn_id = f"TXN-{random.randint(100000000000, 999999999999)}"
    amount = float(random.randint(100, 100000))
    
    txn_date_obj = datetime.now() - timedelta(days=random.randint(1, 45))
    txn_date = txn_date_obj.strftime("%Y-%m-%d")
    txn_time = txn_date_obj.strftime("%H:%M")
    
    # Priority
    priority = "MEDIUM"
    if amount > 50000:
        priority = "HIGH"
    elif amount < 1000:
        priority = "LOW"
    if category == "Unauthorized Transaction":
        priority = "HIGH" if amount > 10000 else "MEDIUM"
        
    status = random.choice(["Dispute Raised", "Under Investigation", "Pending Documents", "Resolved", "Rejected", "Closed"])
    
    db_case = DisputeCase(
        case_id=case_id,
        customer_id=customer.customer_id,
        customer_name=customer.full_name,
        email=customer.email,
        phone=customer.phone,
        transaction_id=txn_id,
        transaction_type=random.choice(["UPI", "Debit Card", "Credit Card", "Net Banking"]),
        merchant=merchant.merchant_name,
        amount=amount,
        currency="INR",
        transaction_date=txn_date,
        transaction_time=txn_time,
        customer_comment=f"I am filing a dispute regarding {reason} for amount INR {amount}.",
        dispute_reason=reason,
        fraud_selected=(category in ["Unauthorized Transaction", "Friendly Fraud"]),
        dispute_category=category,
        fraud_suspicion=(category == "Unauthorized Transaction"),
        customer_intent_summary=f"Customer disputes txn because of {reason}.",
        priority=priority,
        confidence_score=random.uniform(0.7, 0.99),
        risk_tags=json.dumps(["High Amount"] if amount > 50000 else []),
        structured_reasoning="Auto-generated dispute case from bulk seeding.",
        status=status,
        workflow_ready=True,
        current_stage="resolution" if status in ["Resolved", "Rejected", "Closed"] else "investigation",
        assigned_queue=random.choice(["High Value Queue", "Standard Queue", "VIP Queue"]),
        assigned_analyst=random.choice(["analyst.one@bank.com", "analyst.two@bank.com", None]),
        priority_score=random.uniform(1.0, 5.0),
        sla_deadline=datetime.now(timezone.utc) + timedelta(days=random.randint(1, 7)),
        sla_breached=False,
        evidence_match=random.choice([True, False, None]),
        created_at=txn_date_obj,
        updated_at=datetime.now(timezone.utc)
    )
    
    txn = Transaction(
        transaction_id=txn_id,
        customer_id=customer.customer_id,
        merchant_id=merchant.merchant_id,
        merchant_name=merchant.merchant_name,
        amount=amount,
        currency="INR",
        transaction_type=db_case.transaction_type,
        transaction_date=txn_date_obj,
        status="Success",
        is_disputed=True,
        created_at=txn_date_obj
    )
    
    return db_case, txn

def seed_db():
    print("Connecting to database...")
    db = SessionLocal()
    
    # 1. Check existing numbers
    existing_merchants_count = db.query(MerchantProfile).count()
    existing_customers_count = db.query(BankCustomer).count()
    existing_cases_count = db.query(DisputeCase).count()
    
    print(f"Current state: Merchants: {existing_merchants_count}, Customers: {existing_customers_count}, Cases: {existing_cases_count}")
    
    # 2. Add 100 new merchants
    print("Generating 100 new merchants...")
    new_merchants = []
    merchant_start_idx = existing_merchants_count + 1
    for i in range(100):
        m = generate_random_merchant(merchant_start_idx + i)
        db.add(m)
        new_merchants.append(m)
    db.commit()
    print("100 merchants added successfully.")
    
    # 3. Add 1000 new customers
    print("Generating 1000 new customers...")
    new_customers = []
    customer_start_idx = existing_customers_count + 1
    for i in range(1000):
        c = generate_random_customer(customer_start_idx + i)
        db.add(c)
        new_customers.append(c)
    db.commit()
    print("1000 customers added successfully.")
    
    # Fetch all merchants and customers (including existing ones)
    all_merchants = db.query(MerchantProfile).all()
    all_customers = db.query(BankCustomer).all()
    
    # 4. Enhance the first 20 cases
    print("Enhancing the first 20 cases with proper evidences...")
    first_20_cases = db.query(DisputeCase).order_by(DisputeCase.id).limit(20).all()
    
    # We will map each of the first 20 cases to cover all categories
    for idx, case in enumerate(first_20_cases):
        category = CATEGORIES[idx % len(CATEGORIES)]
        reason = random.choice(CATEGORY_REASONS[category])
        case.dispute_category = category
        case.dispute_reason = reason
        case.customer_comment = f"Filing claim for {reason}. I have uploaded all the required documents to verify this."
        case.fraud_selected = (category in ["Unauthorized Transaction", "Friendly Fraud"])
        case.fraud_suspicion = (category == "Unauthorized Transaction")
        case.evidence_match = True
        case.evidence_match_note = f"All submitted documents match and confirm the claim details of {category} dispute."
        
        # Realistic evidence assessment
        evidence_docs_info = []
        req_docs = REQUIRED_DOCUMENTS[category]
        for doc in req_docs:
            evidence_docs_info.append({
                "document_type": doc,
                "status": "VERIFIED",
                "extracted_metadata": {
                    "matched_merchant": case.merchant,
                    "matched_amount": case.amount,
                    "matched_date": case.transaction_date
                }
            })
            
        case.evidence_assessment = {
            "evidence_match": True,
            "strength_score": 0.95,
            "overall_notes": "Highly strong evidence. All customer documents submitted and validated against transaction records.",
            "verified_documents": evidence_docs_info,
            "tools_used": ["verify_ocr_content", "match_amount_and_merchant", "check_bank_statement_integrity"],
            "agent_metadata": {
                "agent_name": "Evidence Intelligence Agent",
                "agent_version": "1.2.0",
                "model": "gemini-3.5-flash",
                "execution_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Trust Intelligence
        case.user_trust_score = 0.98 if category != "Friendly Fraud" else 0.45
        case.behavioral_risk_score = 0.02 if category != "Friendly Fraud" else 0.75
        case.identity_status = "VERIFIED"
        case.trust_intelligence = {
            "user_trust_score": case.user_trust_score,
            "behavioral_risk_score": case.behavioral_risk_score,
            "identity_verification": "VERIFIED",
            "fraud_risk_level": "LOW" if category != "Friendly Fraud" else "HIGH",
            "kyc_checks": {
                "name_match": True,
                "contact_match": True,
                "address_match": True
            },
            "device_fingerprint": {
                "recognized_device": True,
                "location_consistent": True,
                "device_risk": "LOW"
            },
            "dispute_behavior": {
                "prior_dispute_count": random.randint(0, 2),
                "friendly_fraud_risk": "LOW" if category != "Friendly Fraud" else "HIGH"
            }
        }
        
        case.status = "Under Investigation"
        case.current_stage = "investigation"
        case.assigned_analyst = f"analyst.{idx+1}@bank.com"
        
        # Clear existing unfulfilled document requests to avoid duplicates
        db.query(DocumentRequest).filter(DocumentRequest.case_id == case.case_id).delete()
        
        # Insert fulfilled DocumentRequests for these documents
        for doc in req_docs:
            dr = DocumentRequest(
                case_id=case.case_id,
                requested_by="System",
                document_type=doc,
                description=f"Required for {category}",
                fulfilled=True,
                fulfilled_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 12))
            )
            db.add(dr)
            
        # Add audit log
        db.add(AuditLog(
            case_id=case.case_id,
            event_type="DOCUMENT_UPLOADED",
            stage="customer_action",
            actor="customer",
            message=f"Customer uploaded all {len(req_docs)} required document(s) for {category}.",
            payload={"uploaded_documents": req_docs}
        ))
        
    db.commit()
    print("Enhanced first 20 cases updated successfully with proper evidences.")
    
    # 5. Bulk insert 9,980 new dispute cases and transactions to make total cases = 10,000
    target_total_cases = 10000
    cases_needed = target_total_cases - existing_cases_count
    
    if cases_needed <= 0:
        print("We already have 10,000 or more cases.")
    else:
        print(f"Generating and bulk-inserting {cases_needed} cases to reach exactly {target_total_cases} dispute cases...")
        
        batch_size = 500
        cases_buffer = []
        txns_buffer = []
        
        case_id_start = existing_cases_count + 1
        
        for k in range(cases_needed):
            curr_case_id_idx = case_id_start + k
            c_case, c_txn = generate_random_dispute(curr_case_id_idx, all_customers, all_merchants)
            cases_buffer.append(c_case)
            txns_buffer.append(c_txn)
            
            if len(cases_buffer) >= batch_size or k == cases_needed - 1:
                # Add to DB
                db.add_all(txns_buffer)
                db.add_all(cases_buffer)
                db.commit()
                
                # Add basic audit log for the batch
                for cs in cases_buffer:
                    db.add(AuditLog(
                        case_id=cs.case_id,
                        event_type="CASE_RECEIVED",
                        stage="intake",
                        actor="system",
                        message="Dispute case ingested via bulk loader.",
                        created_at=cs.created_at
                    ))
                db.commit()
                
                print(f"Successfully processed {k + 1} / {cases_needed} cases...")
                cases_buffer.clear()
                txns_buffer.clear()
                
    # Verify counts again
    print("Verifying final database counts...")
    final_customers = db.query(BankCustomer).count()
    final_merchants = db.query(MerchantProfile).count()
    final_txns = db.query(Transaction).count()
    final_cases = db.query(DisputeCase).count()
    
    print("---------------------------------------------")
    print(f"Verification Results:")
    print(f"Bank Customers: {final_customers} (Expected ~2002)")
    print(f"Merchant Profiles: {final_merchants} (Expected ~200)")
    print(f"Transactions: {final_txns} (Expected ~19981)")
    print(f"Dispute Cases: {final_cases} (Expected ~10000)")
    print("---------------------------------------------")
    
    db.close()
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_db()
