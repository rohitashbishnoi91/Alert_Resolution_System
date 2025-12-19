"""All AARS agents"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from state import AgentState
from tools import *
import json
import re


def create_investigator_agent(model):
    """Create the Investigator agent with DB query tools"""
    system_prompt = """You are the AARS Investigator Agent.

Your role: Query transaction databases and historical data to gather factual evidence.

Available tools:
- db_query_history: Get historical transactions and patterns
- check_linked_accounts: Find related accounts
- check_account_dormancy: Check if account is dormant

Instructions:
1. Based on the alert scenario, use appropriate tools to gather transaction data
2. Report findings in clear, factual format
3. Focus on quantitative data: amounts, frequencies, patterns
4. Always return your findings as a structured summary

Format your final response as:
INVESTIGATOR FINDINGS:
- [Key finding 1]
- [Key finding 2]
..."""

    tools = [db_query_history, check_linked_accounts, check_account_dormancy]
    agent = create_agent(model, tools, system_prompt=system_prompt)
    
    def investigator_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("Investigator Agent Activated")
        print("="*80)
        
        alert_data = state["alert_data"]
        query = f"""Alert ID: {alert_data['alert_id']}
Scenario: {alert_data['scenario_code']} - {alert_data['scenario_name']}
Customer: {alert_data['subject_id']}
Details: {alert_data['trigger_details']}

Investigate this alert using available database tools."""

        try:
            result = agent.invoke({"messages": [HumanMessage(content=query)]})
            findings_text = result["messages"][-1].content
            
            return {
                "findings": [f"[Investigator] {findings_text}"],
                "messages": [AIMessage(content=f"Investigator completed")],
                "next": "supervisor"
            }
        except Exception as e:
            print(f"❌ Investigator failed: {str(e)}")
            print("💾 State saved to checkpoint - can retry later")
            # Return partial state - checkpoint will save it
            return {
                "findings": [f"[Investigator] ERROR: {str(e)}"],
                "messages": [AIMessage(content=f"Investigator failed - retrying...")],
                "next": "investigator"  # Retry investigator
            }
    
    return investigator_node


def create_context_gatherer_agent(model):
    """Create the Context Gatherer agent"""
    system_prompt = """You are the AARS Context Gatherer Agent.

Your role: Gather contextual information including KYC profiles, sanctions data, and adverse media.

Available tools:
- get_kyc_profile: Retrieve customer KYC/profile data
- search_adverse_media: Search for negative news/OSINT
- sanctions_lookup: Check sanctions watchlist

Instructions:
1. Based on the alert scenario, gather relevant contextual data
2. Compare customer profile against transaction patterns
3. Check for compliance issues
4. Report context that helps determine legitimacy

Format your final response as:
CONTEXT GATHERER FINDINGS:
- [Key context 1]
- [Key context 2]
..."""

    tools = [get_kyc_profile, search_adverse_media, sanctions_lookup]
    agent = create_agent(model, tools, system_prompt=system_prompt)
    
    def context_gatherer_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("Context Gatherer Agent Activated")
        print("="*80)
        
        alert_data = state["alert_data"]
        query = f"""Alert ID: {alert_data['alert_id']}
Scenario: {alert_data['scenario_code']} - {alert_data['scenario_name']}
Customer: {alert_data['subject_id']}
Details: {alert_data['trigger_details']}

Gather contextual information using KYC and external data tools."""

        try:
            result = agent.invoke({"messages": [HumanMessage(content=query)]})
            findings_text = result["messages"][-1].content
            
            return {
                "findings": [f"[Context Gatherer] {findings_text}"],
                "messages": [AIMessage(content=f"Context Gatherer completed")],
                "next": "supervisor"
            }
        except Exception as e:
            print(f"❌ Context Gatherer failed: {str(e)}")
            print("💾 State saved to checkpoint - can retry later")
            return {
                "findings": [f"[Context Gatherer] ERROR: {str(e)}"],
                "messages": [AIMessage(content=f"Context Gatherer failed - retrying...")],
                "next": "context_gatherer"  # Retry context gatherer
            }
    
    return context_gatherer_node


def create_adjudicator_agent(model):
    """Create the Adjudicator agent with SOP decision logic"""
    system_prompt = """You are the AARS Adjudicator Agent.

Your role: Make final resolution decisions based on SOPs and gathered evidence.

SOP RULES (CRITICAL - FOLLOW EXACTLY):

A-001 Velocity Spike (Layering):
- IF no prior high velocity in 90 days AND income mismatch → ESCALATE_SAR
- IF velocity spike matches known business cycle → FalsePositive

A-002 Below-Threshold Structuring:
- IF linked accounts aggregate >$28,000 in 7 days → ESCALATE_SAR
- IF deposits geographically diverse AND legitimate business → RFI

A-003 KYC Inconsistency:
- IF occupation is Jeweler/Trader AND transaction to Precious Metals → FalsePositive
- IF occupation is Teacher/Student AND large wire to Precious Metals → ESCALATE_SAR

A-004 Sanctions List Hit:
- IF true entity ID match OR high-risk jurisdiction → ESCALATE_SAR
- IF common name false positive → FalsePositive

A-005 Dormant Account Activation:
- IF KYC risk Low AND RFI available → RFI
- IF KYC risk High OR international withdrawal → ESCALATE_SAR

Instructions:
1. Review ALL findings from Investigator and Context Gatherer
2. Apply the exact SOP rule for the scenario code
3. Output ONLY a JSON resolution:

{
  "action": "ESCALATE_SAR" | "RFI" | "FalsePositive",
  "rationale": "Detailed explanation",
  "confidence": 0.0-1.0,
  "sop_rule_applied": "A-00X rule"
}

Do NOT include any other text. Output ONLY the JSON."""

    agent = create_agent(model, [], system_prompt=system_prompt)
    
    def adjudicator_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("Adjudicator Agent Activated")
        print("="*80)
        
        alert_data = state["alert_data"]
        all_findings = "\n\n".join(state["findings"])
        
        query = f"""Alert ID: {alert_data['alert_id']}
Scenario: {alert_data['scenario_code']} - {alert_data['scenario_name']}

ALL GATHERED EVIDENCE:
{all_findings}

Based on the SOP rules for {alert_data['scenario_code']}, make your final resolution decision.
Output ONLY the JSON resolution format."""

        try:
            result = agent.invoke({"messages": [HumanMessage(content=query)]})
            resolution_text = result["messages"][-1].content
            
            try:
                json_match = re.search(r'\{[\s\S]*\}', resolution_text)
                resolution_json = json.loads(json_match.group() if json_match else resolution_text)
            except:
                resolution_json = {
                    "action": "RFI",
                    "rationale": resolution_text,
                    "confidence": 0.7,
                    "sop_rule_applied": alert_data['scenario_code']
                }
            
            return {
                "resolution": resolution_json,
                "findings": [f"[Adjudicator] Decision: {resolution_json['action']}"],
                "messages": [AIMessage(content=f"Adjudicator completed")],
                "next": "aem_executor"
            }
        except Exception as e:
            print(f"❌ Adjudicator failed: {str(e)}")
            print("💾 State saved to checkpoint - can retry later")
            return {
                "findings": [f"[Adjudicator] ERROR: {str(e)}"],
                "messages": [AIMessage(content=f"Adjudicator failed - retrying...")],
                "next": "adjudicator"  # Retry adjudicator
            }
    
    return adjudicator_node


def create_supervisor_node(model, members):
    """Create the Supervisor/Orchestrator node"""
    def supervisor_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("Supervisor Activated")
        print("="*80)
        
        findings = state.get("findings", [])
        resolution = state.get("resolution", {})
        
        investigator_done = any("Investigator" in f for f in findings)
        context_done = any("Context Gatherer" in f for f in findings)
        adjudicator_done = bool(resolution)
        
        if not investigator_done:
            next_agent = "investigator"
        elif not context_done:
            next_agent = "context_gatherer"
        elif not adjudicator_done:
            next_agent = "adjudicator"
        else:
            next_agent = "FINISH"
        
        print(f"Routing to: {next_agent}")
        
        return {
            "next": next_agent,
            "messages": [AIMessage(content=f"Routing to {next_agent}")]
        }
    
    return supervisor_node


def create_aem_executor_node():
    """AEM Executor - Simulates action execution"""
    def aem_executor_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("Action Execution Module (AEM)")
        print("="*80)
        
        alert_data = state["alert_data"]
        resolution = state["resolution"]
        action = resolution["action"]
        customer_name = alert_data.get("customer_name", "Customer")
        
        print(f"\n Alert: {alert_data['alert_id']}")
        print(f" Decision: {action}")
        print(f" Rationale: {resolution['rationale']}")
        print(f" Confidence: {resolution['confidence']}")
        
        # Execute action based on decision (exact format per specification)
        if action == "RFI":
            print(f"\nAction Executed: RFI via Email. Drafted message for Customer: {customer_name} requesting Source of Funds.")
        elif action == "ESCALATE_SAR":
            print(f"\nAction Executed: SAR Preparer Module Activated. Case {alert_data['alert_id']} pre-populated and routed to Human Queue. Rationale: {resolution['rationale']}")
        elif action == "FalsePositive":
            print(f"\nAction Executed: Alert {alert_data['alert_id']} closed as False Positive. No further action required.")
        
        # Check if IVR is needed (for A-005 Dormant Account scenario)
        if alert_data.get('scenario_code') == 'A-005' and action == "RFI":
            print(f"Action Executed: IVR Call Initiated. Script ID 3 used for simple verification. Awaiting Customer Response...")
        
        print("\n" + "="*80)
        
        return {
            "next": "END",
            "messages": [AIMessage(content=f"AEM executed: {action}")]
        }
    
    return aem_executor_node

