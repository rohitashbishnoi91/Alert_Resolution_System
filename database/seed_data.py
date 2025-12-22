"""Database Seed Script"""

from datetime import datetime
from database.connection import get_db_session, init_db
from database.models import Customer, Transaction, Alert

# Mock data embedded here
MOCK_CUSTOMER_DB = {
    "CUST-101": {
        "customer_id": "CUST-101",
        "name": "Rohitash",
        "occupation": "Teacher",
        "declared_income": 50000,
        "account_open_date": "2020-03-15",
        "risk_rating": "Low",
        "kyc_verified": True,
        "employer": "Delhi Public School"
    },
    "CUST-102": {
        "customer_id": "CUST-102",
        "name": "Priya",
        "occupation": "Jeweler",
        "declared_income": 120000,
        "account_open_date": "2018-06-20",
        "risk_rating": "Medium",
        "kyc_verified": True,
        "employer": "Sharma Fine Jewelry Pvt Ltd"
    },
    "CUST-103": {
        "customer_id": "CUST-103",
        "name": "Rajesh Traders Pvt Ltd",
        "occupation": "Construction Business",
        "declared_income": 500000,
        "account_open_date": "2019-01-10",
        "risk_rating": "Low",
        "kyc_verified": True,
        "employer": "Self-Employed"
    },
    "CUST-104": {
        "customer_id": "CUST-104",
        "name": "Anjali",
        "occupation": "Freelance Consultant",
        "declared_income": 75000,
        "account_open_date": "2021-05-12",
        "risk_rating": "Medium",
        "kyc_verified": True,
        "employer": "Self-Employed"
    },
    "CUST-105": {
        "customer_id": "CUST-105",
        "name": "Vikram",
        "occupation": "Retired",
        "declared_income": 30000,
        "account_open_date": "2015-08-05",
        "risk_rating": "High",
        "kyc_verified": False,
        "employer": "N/A"
    }
}

MOCK_TRANSACTION_HISTORY = {
    "CUST-101": [
        {"date": "2024-09-15", "amount": 1200, "type": "debit", "description": "Rent payment"},
        {"date": "2024-10-01", "amount": 800, "type": "debit", "description": "Utilities"},
        {"date": "2024-11-05", "amount": 1500, "type": "credit", "description": "Salary deposit"},
        {"date": "2024-11-20", "amount": 900, "type": "debit", "description": "Groceries/misc"}
    ],
    "CUST-102": [
        {"date": "2024-09-10", "amount": 9200, "type": "credit", "description": "Cash deposit - Branch A"},
        {"date": "2024-09-12", "amount": 9500, "type": "credit", "description": "Cash deposit - Branch A"},
        {"date": "2024-09-15", "amount": 9800, "type": "credit", "description": "Cash deposit - Branch B"},
        {"date": "2024-10-01", "amount": 15000, "type": "debit", "description": "Supplier payment"}
    ],
    "CUST-103": [
        {"date": "2024-06-01", "amount": 45000, "type": "credit", "description": "Project payment"},
        {"date": "2024-07-15", "amount": 38000, "type": "credit", "description": "Project payment"},
        {"date": "2024-09-01", "amount": 52000, "type": "credit", "description": "Project payment"},
        {"date": "2024-12-01", "amount": 48000, "type": "credit", "description": "Inbound wire"},
        {"date": "2024-12-01", "amount": 8500, "type": "debit", "description": "Wire transfer"},
        {"date": "2024-12-02", "amount": 7200, "type": "debit", "description": "Wire transfer"},
        {"date": "2024-12-02", "amount": 9100, "type": "debit", "description": "Wire transfer"},
        {"date": "2024-12-03", "amount": 6800, "type": "debit", "description": "Wire transfer"},
        {"date": "2024-12-03", "amount": 11500, "type": "debit", "description": "Wire transfer"}
    ],
    "CUST-104": [
        {"date": "2024-08-15", "amount": 5500, "type": "credit", "description": "Client payment"},
        {"date": "2024-09-20", "amount": 6200, "type": "credit", "description": "Client payment"},
        {"date": "2024-10-10", "amount": 4800, "type": "credit", "description": "Client payment"}
    ],
    "CUST-105": [
        {"date": "2023-06-10", "amount": 2500, "type": "credit", "description": "Social security"},
        {"date": "2023-07-10", "amount": 2500, "type": "credit", "description": "Social security"},
        {"date": "2023-08-10", "amount": 2500, "type": "credit", "description": "Social security"}
    ]
}

TEST_ALERTS = [
    {
        "alert_id": "ALT-2024-001",
        "scenario_code": "A-001",
        "scenario_name": "Velocity Spike (Layering)",
        "subject_id": "CUST-101",
        "trigger_details": "5 transactions exceeding $5,000 within 48 hours (total: $42,800). Large inbound credit of $48,000 received 2 hours prior to first outbound.",
        "expected_action": "ESCALATE_SAR"
    },
    {
        "alert_id": "ALT-2024-002",
        "scenario_code": "A-002",
        "scenario_name": "Below-Threshold Structuring",
        "subject_id": "CUST-102",
        "trigger_details": "3 cash deposits in 7 days: $9,200 (Branch A), $9,500 (Branch A), $9,800 (Branch B). Total: $28,500.",
        "expected_action": "ESCALATE_SAR"
    },
    {
        "alert_id": "ALT-2024-003",
        "scenario_code": "A-003",
        "scenario_name": "KYC Inconsistency (Business vs. Transaction)",
        "subject_id": "CUST-102",
        "trigger_details": "Individual profile sending $20,000 wire to MCC code 'Precious Metals Trading'.",
        "expected_action": "FalsePositive"
    },
    {
        "alert_id": "ALT-2024-004",
        "scenario_code": "A-004",
        "scenario_name": "Sanctions List Hit (CONFIRMED TERRORIST)",
        "subject_id": "CUST-104",
        "trigger_details": "Transaction counterparty 'Mahmoud Al-Hassan' is CONFIRMED 98% match to OFAC SDN List - TERRORIST designation. Immediate action required.",
        "counterparty_name": "Mahmoud Al-Hassan",
        "expected_action": "BLOCK_ACCOUNT"
    },
    {
        "alert_id": "ALT-2024-005",
        "scenario_code": "A-005",
        "scenario_name": "Dormant Account Activation",
        "subject_id": "CUST-105",
        "trigger_details": "Account dormant 16 months. Received $15,000 inbound wire, followed by $12,000 ATM withdrawal (international location).",
        "expected_action": "ESCALATE_SAR"
    }
]


def seed_database():
    """Populate database with mock data"""
    
    print("\n" + "="*60)
    print("SEEDING DATABASE")
    print("="*60 + "\n")
    
    init_db()
    
    with get_db_session() as db:
        # Clear existing data
        print("Clearing existing data...")
        db.query(Alert).delete()
        db.query(Transaction).delete()
        db.query(Customer).delete()
        db.commit()
        
        # Seed customers
        print("Seeding customers...")
        for customer_data in MOCK_CUSTOMER_DB.values():
            # Create customer with id field set to customer_id
            cust_data = customer_data.copy()
            cust_data['id'] = cust_data['customer_id']  # Set primary key
            customer = Customer(**cust_data)
            db.add(customer)
        db.commit()
        print(f"  ✓ Seeded {len(MOCK_CUSTOMER_DB)} customers")
        
        # Seed transactions
        print("Seeding transactions...")
        count = 0
        for customer_id, transactions in MOCK_TRANSACTION_HISTORY.items():
            for idx, txn_data in enumerate(transactions, 1):
                # Generate transaction ID
                txn_id = f"TXN-{customer_id}-{idx:03d}"
                
                # Parse date string to datetime
                date_str = txn_data.get("date")
                date_obj = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.utcnow()
                
                transaction = Transaction(
                    id=txn_id,
                    customer_id=customer_id,
                    amount=txn_data.get("amount", 0),
                    type=txn_data.get("type", "UNKNOWN"),
                    date=date_obj,
                    counterparty=txn_data.get("description", "")
                )
                db.add(transaction)
                count += 1
        db.commit()
        print(f"  ✓ Seeded {count} transactions")
        
        # Seed alerts
        print("Seeding alerts...")
        for alert_data in TEST_ALERTS:
            alert = Alert(
                id=alert_data["alert_id"],
                customer_id=alert_data["subject_id"],
                scenario_code=alert_data["scenario_code"],
                scenario_name=alert_data["scenario_name"],
                description=alert_data.get("description", ""),
                trigger_details=alert_data["trigger_details"],
                status="PENDING"
            )
            db.add(alert)
        db.commit()
        print(f"  ✓ Seeded {len(TEST_ALERTS)} alerts")
    
    print("\n" + "="*60)
    print("DATABASE SEEDING COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    seed_database()
