"""Agent state definition"""

from typing import TypedDict, Annotated, Optional
import operator


class AgentState(TypedDict):
    """Shared state across all agents in the AARS workflow"""
    alert_data: dict
    findings: Annotated[list, operator.add]  # Accumulates via reducer
    resolution: dict
    next: str
    messages: Annotated[list, operator.add]  # Accumulates via reducer
    # Conversation mode fields
    mode: str  # "resolve" or "conversation"
    user_query: str  # User's current question
    conversation_history: Annotated[list, operator.add]  # Accumulates via reducer - persisted in checkpoint!
    conversation_response: str  # Latest response from conversational agent

