from agents.dispute_agent.state import DisputeAgentState


def _yn(val) -> str:
    if val is True:  return "Yes"
    if val is False: return "No"
    return str(val) if val else "Not provided"


def build_evidence(state: DisputeAgentState) -> dict:
    meta = state["dispute_input"].get("transaction_metadata") or {}

    evidence = (
        f"  OTP Received (for this txn)  : {_yn(meta.get('otp_received'))}\n"
        f"  Card / Account Blocked       : {_yn(meta.get('card_blocked'))}\n"
        f"  Bank Already Contacted       : {_yn(meta.get('bank_contacted'))}\n"
        f"  Transaction Location         : {meta.get('transaction_location') or 'Not provided'}\n"
        f"  OTP Shared with 3rd Party    : {_yn(meta.get('otp_shared'))}\n"
        f"  Bank Impersonation Call      : {_yn(meta.get('bank_impersonation'))}\n"
        f"  Remote Access App Installed  : {_yn(meta.get('remote_access'))}\n"
        f"  Phishing Link Clicked        : {_yn(meta.get('phishing_link'))}\n"
        f"  SIM Swap Suspected           : {_yn(meta.get('sim_swap_suspected'))}\n"
        f"  Device Lost / Stolen         : {_yn(meta.get('device_lost'))}\n"
        f"  Card Lost / Stolen           : {_yn(meta.get('card_lost'))}\n"
        f"  Unknown Beneficiary Added    : {_yn(meta.get('unknown_beneficiary'))}\n"
        f"  UPI Collect Fraud            : {_yn(meta.get('upi_collect_fraud'))}\n"
        f"  Steps Already Taken          : {meta.get('fraud_additional_details') or 'None stated'}\n"
    )

    return {"supporting_evidence": evidence}
