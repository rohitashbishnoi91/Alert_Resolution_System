"""Agent tools - Database queries and external lookups"""

from langchain_core.tools import tool
import json
from database.connection import get_db_session
from database.models import Customer, Transaction

MOCK_SANCTIONS_LIST = {
    "Mahmoud Al-Hassan": {
        "entity_id": "SANC-9001", 
        "jurisdiction": "High-Risk", 
        "match_type": "CONFIRMED TERRORIST - OFAC SDN LIST",
        "list_source": "OFAC SDN",
        "category": "TERRORISM",
        "confidence": 0.98,
        "action_required": "BLOCK_ACCOUNT"
    },
    "Deepak": {
        "entity_id": None, 
        "jurisdiction": "N/A", 
        "match_type": "Common Name - False Positive",
        "list_source": None,
        "category": None,
        "confidence": 0.15,
        "action_required": None
    },
    "Omar Terrorist Inc": {
        "entity_id": "SANC-9002",
        "jurisdiction": "Syria",
        "match_type": "CONFIRMED SANCTIONED ENTITY - UN SANCTIONS",
        "list_source": "UN Security Council",
        "category": "TERRORIST FINANCING",
        "confidence": 0.99,
        "action_required": "BLOCK_ACCOUNT"
    },
    "Viktor Petrov": {
        "entity_id": "SANC-9003",
        "jurisdiction": "Russia",
        "match_type": "CONFIRMED - EU/US SANCTIONS",
        "list_source": "OFAC/EU Consolidated List",
        "category": "SANCTIONED OLIGARCH",
        "confidence": 0.95,
        "action_required": "BLOCK_ACCOUNT"
    }
}

MOCK_ADVERSE_MEDIA = {
    "CUST-101": {"hits": 0, "summary": "No adverse media found for Rohitash"},
    "CUST-102": {"hits": 0, "summary": "No adverse media found for Priya"},
    "CUST-103": {"hits": 0, "summary": "No adverse media found for Rajesh Traders Pvt Ltd"},
    "CUST-104": {"hits": 1, "summary": "1 news article about business dispute (civil matter, resolved) - Anjali"},
    "CUST-105": {"hits": 0, "summary": "No adverse media found for Vikram"}
}


@tool
def db_query_history(customer_id: str, lookback_days: int = 90) -> str:
    """Query historical transaction data for a customer."""
    print(f"\n🔍 [DB Tool] Querying transaction history for {customer_id}")
    
    try:
        with get_db_session() as db:
            transactions = db.query(Transaction).filter(
                Transaction.customer_id == customer_id
            ).all()
            
            if not transactions:
                return json.dumps({"error": "Customer not found", "transactions": []})
            
            txn_list = [t.to_dict() for t in transactions]
            high_value_txns = [t for t in txn_list if t["amount"] > 5000]
            max_txn = max([t["amount"] for t in txn_list]) if txn_list else 0
            avg_txn = sum([t["amount"] for t in txn_list]) / len(txn_list) if txn_list else 0
            
            result = {
                "customer_id": customer_id,
                "transactions": txn_list,
                "historical_max_txn": max_txn,
                "historical_avg_txn": round(avg_txn, 2),
                "high_value_count_90d": len(high_value_txns),
                "total_transactions": len(txn_list)
            }
            
            print(f"   ✓ Found {len(txn_list)} transactions, max: ${max_txn}")
            return json.dumps(result, indent=2)
    
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return json.dumps({"error": str(e), "transactions": []})


@tool
def check_linked_accounts(customer_id: str) -> str:
    """Check for linked accounts associated with a customer."""
    print(f"\n🔗 [DB Tool] Checking linked accounts for {customer_id}")
    
    linked = []
    aggregate_deposits = 28500 if customer_id == "CUST-102" else 0
    
    result = {
        "customer_id": customer_id,
        "linked_accounts": linked,
        "linked_account_count": len(linked),
        "aggregate_recent_deposits": aggregate_deposits
    }
    
    print(f"   ✓ Found {len(linked)} linked accounts")
    return json.dumps(result, indent=2)


@tool
def check_account_dormancy(customer_id: str) -> str:
    """Check account dormancy status."""
    print(f"\n💤 [DB Tool] Checking account dormancy for {customer_id}")
    
    try:
        with get_db_session() as db:
            transactions = db.query(Transaction).filter(
                Transaction.customer_id == customer_id
            ).all()
            
            is_dormant = customer_id == "CUST-105"
            dormant_months = 16 if is_dormant else 0
            
            txn_list = [t.to_dict() for t in transactions]
            
            result = {
                "customer_id": customer_id,
                "is_dormant": is_dormant,
                "dormant_months": dormant_months,
                "last_activity_date": txn_list[-1]["date"] if txn_list else "N/A",
                "recent_transactions": txn_list[-5:] if txn_list else []
            }
            
            print(f"   ✓ Dormant: {is_dormant}, Months: {dormant_months}")
            return json.dumps(result, indent=2)
    
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return json.dumps({"error": str(e)})


@tool
def get_kyc_profile(customer_id: str) -> str:
    """Retrieve KYC profile from database."""
    print(f"\n👤 [Context Tool] Retrieving KYC profile for {customer_id}")
    
    try:
        with get_db_session() as db:
            customer = db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return json.dumps({"error": "Customer not found"})
            
            profile = customer.to_dict()
            print(f"   ✓ Profile: {profile['occupation']}, Income: ${profile['declared_income']}")
            return json.dumps(profile, indent=2)
    
    except Exception as e:
        print(f"   ✗ Database error: {e}")
        return json.dumps({"error": str(e)})


@tool
def search_adverse_media(customer_id: str) -> str:
    """Search for adverse media mentions."""
    print(f"\n📰 [Context Tool] Searching adverse media for {customer_id}")
    
    result = MOCK_ADVERSE_MEDIA.get(customer_id, {"hits": 0, "summary": "No data available"})
    print(f"   ✓ Adverse media hits: {result['hits']}")
    return json.dumps(result, indent=2)


@tool
def sanctions_lookup(counterparty_name: str) -> str:
    """Look up counterparty in sanctions watchlist (OFAC, UN, EU)."""
    print(f"\n🚨 [Context Tool] Sanctions lookup for '{counterparty_name}'")
    
    result = MOCK_SANCTIONS_LIST.get(counterparty_name, {
        "entity_id": None,
        "jurisdiction": "N/A",
        "match_type": "No Match",
        "list_source": None,
        "category": None,
        "confidence": 0.0,
        "action_required": None
    })
    
    result["counterparty_name"] = counterparty_name
    is_confirmed = result.get("action_required") == "BLOCK_ACCOUNT"
    
    if is_confirmed:
        print(f"   ⛔ CONFIRMED MATCH: {result['match_type']}")
        print(f"   ⛔ List: {result['list_source']}, Category: {result['category']}")
        print(f"   ⛔ RECOMMENDED ACTION: BLOCK_ACCOUNT")
    else:
        print(f"   ✓ Match type: {result['match_type']}")
    
    return json.dumps(result, indent=2)
