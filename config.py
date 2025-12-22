"""Configuration settings"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.1

SCENARIOS = {
    "A-001": "Velocity Spike (Layering)",
    "A-002": "Below-Threshold Structuring",
    "A-003": "KYC Inconsistency",
    "A-004": "Sanctions List Hit",
    "A-005": "Dormant Account Activation"
}

ACTIONS = ["ESCALATE_SAR", "RFI", "FalsePositive", "BLOCK_ACCOUNT"]
