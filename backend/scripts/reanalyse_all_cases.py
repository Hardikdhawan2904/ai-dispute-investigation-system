"""
Bulk re-analysis script — re-runs all three agents on every case in the DB.

Run this whenever agent prompts or logic are updated to apply the changes
to all existing cases:

    cd backend
    python scripts/reanalyse_all_cases.py

Options:
    --status   only re-analyse cases with this status  (e.g. --status "Pending Documents")
    --case     re-analyse a single case               (e.g. --case CASE-000527)
    --dry-run  list cases that would be re-analysed without running
"""
import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal
from database.models import DisputeCase, AuditLog
from agents.dispute_agent import run_dispute_agent
from agents.investigation_agent import run_investigation_agent
from agents.orchestration_agent import run_orchestration_agent
from workflows.dispute_workflow import _save_agent1_to_db, _save_agent2_to_db, _save_agent3_to_db
from services.priority_engine import compute_priority
from services.queue_assignment_service import assign_queue
from services.sla_service import compute_sla_deadline
from services.manual_review_service import should_flag_manual_review
from services.document_rules import resolve_investigation_status
from utils.extractor import extract_text
from utils.logger import api_logger

_UPLOADS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
_ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".xlsx", ".csv"}


def _extract_documents(case_id: str) -> list:
    case_dir = os.path.join(_UPLOADS_ROOT, case_id)
    if not os.path.exists(case_dir):
        return []
    texts = []
    for fname in sorted(os.listdir(case_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in _ALLOWED_EXTS:
            text = extract_text(os.path.join(case_dir, fname))
            if text.strip():
                texts.append(f"[{fname}]\n{text}")
    return texts


def reanalyse_case(case_id: str) -> bool:
    """Run all 3 agents on a single case. Returns True on success."""
    print(f"  [{case_id}] Running Agent 1 (ARIA)...", end="", flush=True)
    t0 = time.time()
    try:
        doc_texts = _extract_documents(case_id)
        result1 = run_dispute_agent({}, case_id=case_id, document_texts=doc_texts)
        _save_agent1_to_db(case_id, result1)
        print(f" {time.time()-t0:.1f}s  tags={result1.get('risk_tags')}", flush=True)
    except Exception as e:
        print(f" FAILED: {e}", flush=True)
        return False

    print(f"  [{case_id}] Running Agent 2 (IIA)...", end="", flush=True)
    t0 = time.time()
    try:
        result2 = run_investigation_agent({"case_id": case_id})
        if result2:
            _save_agent2_to_db(case_id, result2)
        print(f" {time.time()-t0:.1f}s  queue={result2.get('recommended_queue') if result2 else 'N/A'}", flush=True)
    except Exception as e:
        print(f" FAILED: {e}", flush=True)

    print(f"  [{case_id}] Running Agent 3 (WOA)...", end="", flush=True)
    t0 = time.time()
    try:
        result3 = run_orchestration_agent(case_id)
        if result3:
            _save_agent3_to_db(case_id, result3)
        print(f" {time.time()-t0:.1f}s  path={result3.get('workflow_path') if result3 else 'N/A'}", flush=True)
    except Exception as e:
        print(f" FAILED: {e}", flush=True)

    # Recompute priority, queue, SLA, manual review
    db = SessionLocal()
    try:
        case = db.query(DisputeCase).filter(DisputeCase.case_id == case_id).first()
        if not case:
            return False
        case.status = resolve_investigation_status(case, case_id)
        priority_score, priority_label = compute_priority(case.to_dict())
        case.priority       = priority_label
        case.priority_score = priority_score
        case.assigned_queue = assign_queue(case.to_dict())
        case.sla_deadline   = compute_sla_deadline(priority_label)
        flag, reason = should_flag_manual_review(case.to_dict())
        case.requires_manual_review = flag
        case.manual_review_reason   = reason if flag else None
        db.add(AuditLog(
            case_id=case_id,
            event_type="BULK_REANALYSED",
            stage="bulk_update",
            actor="system",
            message="Re-analysed by bulk reanalysis script after agent update.",
        ))
        db.commit()
        print(f"  [{case_id}] Done — priority={priority_label} queue={case.assigned_queue}", flush=True)
    except Exception as e:
        db.rollback()
        print(f"  [{case_id}] Save failed: {e}", flush=True)
        return False
    finally:
        db.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Bulk re-analyse all cases with updated agents")
    parser.add_argument("--status",  help="Filter by case status")
    parser.add_argument("--case",    help="Re-analyse a single case ID")
    parser.add_argument("--dry-run", action="store_true", help="List cases without running")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        q = db.query(DisputeCase)
        if args.case:
            q = q.filter(DisputeCase.case_id == args.case)
        if args.status:
            q = q.filter(DisputeCase.status == args.status)
        cases = q.order_by(DisputeCase.created_at).all()
        case_ids = [c.case_id for c in cases]
    finally:
        db.close()

    if not case_ids:
        print("No cases matched.")
        return

    print(f"\nCases to re-analyse ({len(case_ids)}): {case_ids}")
    if args.dry_run:
        return

    print()
    ok = fail = 0
    for cid in case_ids:
        print(f"\n--- {cid} ---")
        if reanalyse_case(cid):
            ok += 1
        else:
            fail += 1

    print(f"\nComplete: {ok} succeeded, {fail} failed.")


if __name__ == "__main__":
    main()
