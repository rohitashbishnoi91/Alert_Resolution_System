"""
Alert Scenario Definitions
Pre-defined test cases for the Alert Resolution System
"""

from typing import List, Dict, Any


# 5 Authoritative Alert Scenarios
ALERT_SCENARIOS: List[Dict[str, Any]] = [
    {
        "alert_id": "A-001",
        "scenario_code": "VELOCITY_SPIKE",
        "subject_id": "CUST-101",
        "description": "Velocity Spike (Layering) - 5+ transactions > $5k within 48 hours",
    },
    {
        "alert_id": "A-002",
        "scenario_code": "STRUCTURING",
        "subject_id": "CUST-102",
        "description": "Below-Threshold Structuring - 3 cash deposits in 7 days between $9k-$9.9k",
    },
    {
        "alert_id": "A-003",
        "scenario_code": "KYC_INCONSISTENCY",
        "subject_id": "CUST-103",
        "description": "KYC Inconsistency - Teacher wiring $20k to Precious Metals Trading",
    },
    {
        "alert_id": "A-004",
        "scenario_code": "SANCTIONS_HIT",
        "subject_id": "CUST-104",
        "description": "Sanctions Watchlist Hit - Counterparty fuzzy name match (~80%)",
    },
    {
        "alert_id": "A-005",
        "scenario_code": "DORMANT_REACTIVATION",
        "subject_id": "CUST-105",
        "description": "Dormant Account Reactivation - Dormant 12+ months, $15k wire-in + immediate ATM withdrawal",
    },
]


def get_all_scenarios() -> List[Dict[str, Any]]:
    """Return all alert scenarios"""
    return ALERT_SCENARIOS


def get_scenario_by_id(alert_id: str) -> Dict[str, Any]:
    """Get specific scenario by alert ID"""
    for scenario in ALERT_SCENARIOS:
        if scenario["alert_id"] == alert_id:
            return scenario
    return {}

