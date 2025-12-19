"""LangGraph workflow construction"""

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from state import AgentState
from agents import (
    create_investigator_agent,
    create_context_gatherer_agent,
    create_adjudicator_agent,
    create_supervisor_node,
    create_aem_executor_node
)
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
import os

# Enable checkpoints for fault-tolerance (resume after agent failures)
USE_CHECKPOINTS = os.getenv("USE_CHECKPOINTS", "true").lower() == "true"


def create_aars_workflow():
    """Build the complete LangGraph workflow"""
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment")
    
    model = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        api_key=OPENAI_API_KEY
    )
    
    members = ["investigator", "context_gatherer", "adjudicator"]
    
    investigator = create_investigator_agent(model)
    context_gatherer = create_context_gatherer_agent(model)
    adjudicator = create_adjudicator_agent(model)
    supervisor = create_supervisor_node(model, members)
    aem_executor = create_aem_executor_node()
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("supervisor", supervisor)
    workflow.add_node("investigator", investigator)
    workflow.add_node("context_gatherer", context_gatherer)
    workflow.add_node("adjudicator", adjudicator)
    workflow.add_node("aem_executor", aem_executor)
    
    def route_supervisor(state: AgentState) -> str:
        next_step = state.get("next", "FINISH")
        return END if next_step == "FINISH" else next_step
    
    def route_to_supervisor_or_aem(state: AgentState) -> str:
        return state.get("next", "supervisor")
    
    workflow.set_entry_point("supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "investigator": "investigator",
            "context_gatherer": "context_gatherer",
            "adjudicator": "adjudicator",
            END: END
        }
    )
    
    workflow.add_conditional_edges("investigator", route_to_supervisor_or_aem, {"supervisor": "supervisor"})
    workflow.add_conditional_edges("context_gatherer", route_to_supervisor_or_aem, {"supervisor": "supervisor"})
    workflow.add_conditional_edges("adjudicator", route_to_supervisor_or_aem, {"aem_executor": "aem_executor", "supervisor": "supervisor"})
    workflow.add_edge("aem_executor", END)
    
    # Checkpointing for fault-tolerance and recovery
    if USE_CHECKPOINTS:
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3
        
        db_path = os.getenv("CHECKPOINT_DB", "checkpoints/aars_checkpoints.db")
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else "checkpoints", exist_ok=True)
        
        conn = sqlite3.connect(db_path, check_same_thread=False)
        memory = SqliteSaver(conn)
        app = workflow.compile(checkpointer=memory)
        print("✓ Checkpointing ENABLED - Can resume after failures")
    else:
        # No checkpointing - faster but cannot recover from failures
        app = workflow.compile()
        print("⚠️  Checkpointing DISABLED - Cannot resume after failures")
    
    return app


def run_alert_resolution(app, alert_data, thread_id=None):
    """Run a single alert through the AARS workflow"""
    
    print("\n" + "█"*80)
    print(f"█  AARS WORKFLOW STARTED")
    print(f"█  Alert: {alert_data['alert_id']} | Scenario: {alert_data['scenario_code']}")
    print("█"*80)
    
    initial_state = {
        "alert_data": alert_data,
        "findings": [],
        "resolution": {},
        "next": "",
        "messages": []
    }
    
    config = {"configurable": {"thread_id": thread_id or alert_data['alert_id']}}
    
    final_state = None
    for state in app.stream(initial_state, config):
        final_state = state
    
    resolution = None
    for key, value in final_state.items():
        if "resolution" in value and value["resolution"]:
            resolution = value["resolution"]
            break
    
    print("\n" + "█"*80)
    print(f"█  WORKFLOW COMPLETED")
    if resolution:
        print(f"█  Action: {resolution.get('action', 'N/A')}")
    print("█"*80 + "\n")
    
    return resolution

