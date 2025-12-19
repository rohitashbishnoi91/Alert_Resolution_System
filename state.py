"""Agent state definition"""

from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    """Shared state across all agents in the AARS workflow"""
    alert_data: dict
    findings: Annotated[list, operator.add]
    resolution: dict
    next: str
    messages: Annotated[list, operator.add]

