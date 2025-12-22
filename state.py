"""Agent state definition"""

from typing import TypedDict, Annotated
import operator


class AgentState(TypedDict):
    """Shared state across all agents"""
    alert_data: dict
    findings: Annotated[list, operator.add]
    resolution: dict
    next: str
    messages: Annotated[list, operator.add]
    mode: str
    user_query: str
    conversation_history: Annotated[list, operator.add]
    conversation_response: str
