"""Agent state definition"""

from typing import TypedDict, Annotated, Optional
import operator


class AgentState(TypedDict):
    """Shared state across all agents in the AARS workflow"""
    alert_data: dict
    findings: Annotated[list, operator.add]
    resolution: dict
    next: str
    messages: Annotated[list, operator.add]
    # Conversation mode fields
    mode: str  # "resolve" or "conversation"
    user_query: str  # User's question in conversation mode
    conversation_history: list  # Previous conversation messages
    conversation_response: str  # Response from conversational agent

