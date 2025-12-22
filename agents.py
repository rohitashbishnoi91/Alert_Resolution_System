"""All AARS agents"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from state import AgentState
from tools import *
from database.seed_data import MOCK_CUSTOMER_DB
import json
import re


def create_investigator_agent(model):
    """Investigator agent with DB query tools"""
    system_prompt = """You are the AARS Investigator Agent.

Your role: Query transaction databases and historical data to gather factual evidence.

Available tools:
- db_query_history: Get historical transactions and patterns
- check_linked_accounts: Find related accounts
- check_account_dormancy: Check if account is dormant

Instructions:
1. Use appropriate tools to gather transaction data
2. Report findings in clear, factual format
3. Focus on quantitative data: amounts, frequencies, patterns

Format your response as:
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
            return {
                "findings": [f"[Investigator] ERROR: {str(e)}"],
                "messages": [AIMessage(content=f"Investigator failed - retrying...")],
                "next": "investigator"
            }
    
    return investigator_node


def create_context_gatherer_agent(model):
    """Context Gatherer agent for KYC, sanctions, and adverse media"""
    system_prompt = """You are the AARS Context Gatherer Agent.

Your role: Gather contextual information including KYC profiles, sanctions data, and adverse media.

Available tools:
- get_kyc_profile: Retrieve customer KYC/profile data
- search_adverse_media: Search for negative news/OSINT
- sanctions_lookup: Check sanctions watchlist

Instructions:
1. Gather relevant contextual data
2. Compare customer profile against transaction patterns
3. Check for compliance issues

Format your response as:
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
            return {
                "findings": [f"[Context Gatherer] ERROR: {str(e)}"],
                "messages": [AIMessage(content=f"Context Gatherer failed - retrying...")],
                "next": "context_gatherer"
            }
    
    return context_gatherer_node


def create_adjudicator_agent(model):
    """Adjudicator agent with SOP decision logic"""
    system_prompt = """You are the AARS Adjudicator Agent.

Your role: Make final resolution decisions based on SOPs and gathered evidence.

SOP RULES:

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
- IF CONFIRMED sanctions match (terrorist, OFAC list) → BLOCK_ACCOUNT (IMMEDIATE!)
- IF true entity ID match OR high-risk jurisdiction → ESCALATE_SAR
- IF common name false positive → FalsePositive

A-005 Dormant Account Activation:
- IF KYC risk Low AND RFI available → RFI
- IF KYC risk High OR international withdrawal → ESCALATE_SAR

BLOCK_ACCOUNT: Use ONLY for confirmed sanctions/terrorist matches with >90% confidence.

Output ONLY a JSON resolution:
{
  "action": "ESCALATE_SAR" | "RFI" | "FalsePositive" | "BLOCK_ACCOUNT",
  "rationale": "Detailed explanation",
  "confidence": 0.0-1.0,
  "sop_rule_applied": "A-00X rule"
}"""

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

Based on SOP rules for {alert_data['scenario_code']}, make your final resolution decision.
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
            return {
                "findings": [f"[Adjudicator] ERROR: {str(e)}"],
                "messages": [AIMessage(content=f"Adjudicator failed - retrying...")],
                "next": "adjudicator"
            }
    
    return adjudicator_node


def create_supervisor_node(model, members):
    """Supervisor - LLM-powered orchestrator of the multi-agent system"""
    
    supervisor_prompt = """You are the SUPERVISOR of AARS (Agentic Alert Resolution System).
You are the orchestrating brain that controls a team of specialized agents.

YOUR TEAM:
- investigator: Queries transaction databases, checks linked accounts
- context_gatherer: Retrieves KYC profiles, checks sanctions
- adjudicator: Makes final resolution decisions
- conversational: Answers user questions about alerts

ROUTING RULES:
- If mode is "conversation" → Route to "conversational"
- If no transaction analysis done → Route to "investigator"
- If investigator done but no KYC/sanctions check → Route to "context_gatherer"
- If both done but no decision → Route to "adjudicator"
- If resolution exists → Route to "FINISH"

EMERGENCY: For CONFIRMED sanctions/terrorist match → Route to adjudicator for BLOCK_ACCOUNT

Respond with ONLY a JSON object:
{
    "next": "<agent_name or FINISH>",
    "reasoning": "<brief explanation>"
}

Valid values: investigator, context_gatherer, adjudicator, conversational, FINISH"""

    def supervisor_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("🧠 SUPERVISOR (LLM Brain) Activated")
        print("="*80)
        
        mode = state.get("mode", "resolve")
        findings = state.get("findings", [])
        resolution = state.get("resolution", {})
        alert_data = state.get("alert_data", {})
        user_query = state.get("user_query", "")
        
        findings_summary = "\n".join(findings) if findings else "No findings yet"
        
        decision_prompt = f"""
CURRENT STATE:
- Mode: {mode}
- Alert ID: {alert_data.get('alert_id', 'N/A')}
- Scenario: {alert_data.get('scenario_code', 'N/A')} - {alert_data.get('scenario_name', 'N/A')}
- User Query: {user_query if mode == 'conversation' else 'N/A'}

INVESTIGATION PROGRESS:
{findings_summary}

RESOLUTION STATUS:
{json.dumps(resolution) if resolution else 'No resolution yet'}

Decide which agent should work next. Respond with JSON only."""

        try:
            messages = [
                {"role": "system", "content": supervisor_prompt},
                {"role": "user", "content": decision_prompt}
            ]
            
            response = model.invoke(messages)
            response_text = response.content
            
            try:
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    decision = json.loads(json_match.group())
                    next_agent = decision.get("next", "FINISH")
                    reasoning = decision.get("reasoning", "No reasoning provided")
                else:
                    raise ValueError("No JSON found")
            except (json.JSONDecodeError, ValueError):
                if mode == "conversation":
                    next_agent = "conversational"
                    reasoning = "Fallback: Conversation mode"
                elif not any("Investigator" in f for f in findings):
                    next_agent = "investigator"
                    reasoning = "Fallback: Investigation needed"
                elif not any("Context Gatherer" in f for f in findings):
                    next_agent = "context_gatherer"
                    reasoning = "Fallback: Context needed"
                elif not resolution:
                    next_agent = "adjudicator"
                    reasoning = "Fallback: Adjudication needed"
                else:
                    next_agent = "FINISH"
                    reasoning = "Fallback: Complete"
            
            print(f"🧠 LLM Decision: {next_agent}")
            print(f"💭 Reasoning: {reasoning}")
            
            return {
                "next": next_agent,
                "messages": [AIMessage(content=f"Supervisor: {reasoning}. Routing to {next_agent}")]
            }
            
        except Exception as e:
            print(f"❌ Supervisor error: {str(e)}")
            next_agent = "conversational" if mode == "conversation" else "investigator"
            return {
                "next": next_agent,
                "messages": [AIMessage(content=f"Supervisor fallback to {next_agent}")]
            }
    
    return supervisor_node


def create_aem_executor_node():
    """AEM Executor - executes the final action"""
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
        
        if action == "RFI":
            print(f"\nAction: RFI via Email to {customer_name}")
        elif action == "ESCALATE_SAR":
            print(f"\nAction: SAR filed. Case {alert_data['alert_id']} routed to Human Queue")
        elif action == "FalsePositive":
            print(f"\nAction: Alert {alert_data['alert_id']} closed as False Positive")
        elif action == "BLOCK_ACCOUNT":
            print(f"\n🚫 ACCOUNT BLOCKED!")
            print(f"   ✓ Account {alert_data['subject_id']} FROZEN")
            print(f"   ✓ Sanctions team NOTIFIED")
            print(f"   ✓ Legal escalation initiated")
        
        if alert_data.get('scenario_code') == 'A-005' and action == "RFI":
            print(f"Action: IVR Call Initiated")
        
        print("\n" + "="*80)
        
        return {
            "next": "END",
            "messages": [AIMessage(content=f"AEM executed: {action}")]
        }
    
    return aem_executor_node


def create_conversational_agent(model):
    """Conversational Agent - handles user queries with access to all tools"""
    system_prompt = """You are the AARS Conversational Agent.

Your role: Answer analyst questions about AML alerts conversationally.

Available tools:
- db_query_history: Query transaction history
- check_linked_accounts: Find related accounts
- check_account_dormancy: Check account activity
- get_kyc_profile: Get customer KYC data
- search_adverse_media: Search for negative news
- sanctions_lookup: Check sanctions watchlists

Be conversational, professional, and thorough. You're an AML expert assistant."""

    tools = [
        db_query_history, 
        check_linked_accounts, 
        check_account_dormancy,
        get_kyc_profile, 
        search_adverse_media, 
        sanctions_lookup
    ]
    
    agent = create_agent(model, tools, system_prompt=system_prompt)
    
    def conversational_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("Conversational Agent Activated (Supervisor-controlled)")
        print("="*80)
        
        alert_data = state["alert_data"]
        user_query = state.get("user_query", "")
        conversation_history = state.get("conversation_history", [])
        
        customer_info = MOCK_CUSTOMER_DB.get(alert_data.get('subject_id', ''), {})
        
        context = f"""
ALERT CONTEXT:
- Alert ID: {alert_data.get('alert_id', 'N/A')}
- Scenario: {alert_data.get('scenario_name', 'N/A')} ({alert_data.get('scenario_code', 'N/A')})
- Customer: {alert_data.get('subject_id', 'N/A')}
- Details: {alert_data.get('trigger_details', 'N/A')}

CUSTOMER:
- Name: {customer_info.get('name', 'Unknown')}
- Occupation: {customer_info.get('occupation', 'Unknown')}
- Income: ${customer_info.get('declared_income', 0):,}
- Risk: {customer_info.get('risk_rating', 'Unknown')}
"""
        
        history_text = "(No previous messages)"
        if conversation_history:
            formatted = []
            for msg in conversation_history[-6:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")[:200]
                formatted.append(f"{role}: {content}...")
            history_text = "\n".join(formatted)
        
        full_query = f"""{context}

HISTORY:
{history_text}

USER: {user_query}

Respond helpfully. Use tools if needed."""

        try:
            result = agent.invoke({"messages": [HumanMessage(content=full_query)]})
            response = result["messages"][-1].content
            
            print(f"Query: {user_query[:50]}...")
            print(f"Response generated successfully")
            
            return {
                "conversation_response": response,
                "conversation_history": [
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": response}
                ],
                "messages": [AIMessage(content="Conversational Agent responded")],
                "next": "FINISH"
            }
        except Exception as e:
            print(f"❌ Conversational Agent error: {str(e)}")
            error_response = f"Error: {str(e)}. Please try again."
            return {
                "conversation_response": error_response,
                "conversation_history": [
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": error_response}
                ],
                "messages": [AIMessage(content="Conversational Agent error")],
                "next": "FINISH"
            }
    
    return conversational_node
