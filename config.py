"""Configuration settings"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.1

# Alert Scenarios
SCENARIOS = {
    "A-001": "Velocity Spike (Layering)",
    "A-002": "Below-Threshold Structuring",
    "A-003": "KYC Inconsistency",
    "A-004": "Sanctions List Hit",
    "A-005": "Dormant Account Activation"
}

# Resolution Actions
ACTIONS = ["ESCALATE_SAR", "RFI", "FalsePositive", "BLOCK_ACCOUNT"]

# BLOCK_ACCOUNT: Immediate account blocking for confirmed sanctions/terrorist matches

