"""All AARS agents"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from state import AgentState
from tools import *
from database.seed_data import MOCK_CUSTOMER_DB
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
- IF CONFIRMED sanctions match (terrorist, sanctioned entity, OFAC list) → BLOCK_ACCOUNT (IMMEDIATE!)
- IF true entity ID match OR high-risk jurisdiction → ESCALATE_SAR
- IF common name false positive (low match score, different DOB/country) → FalsePositive

A-005 Dormant Account Activation:
- IF KYC risk Low AND RFI available → RFI
- IF KYC risk High OR international withdrawal → ESCALATE_SAR

CRITICAL - BLOCK_ACCOUNT RULES:
- BLOCK_ACCOUNT is the most severe action - use ONLY when:
  * Customer name is CONFIRMED match on OFAC/UN/EU sanctions list
  * Customer is confirmed terrorist or terrorist-affiliated entity
  * Counterparty is CONFIRMED on sanctions/terrorist watchlist
  * Match confidence is HIGH (>90%) and identity verified
- When BLOCK_ACCOUNT: Immediately freeze all account activity

Instructions:
1. Review ALL findings from Investigator and Context Gatherer
2. Apply the exact SOP rule for the scenario code
3. Output ONLY a JSON resolution:

{
  "action": "ESCALATE_SAR" | "RFI" | "FalsePositive" | "BLOCK_ACCOUNT",
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
    """
    Create the Supervisor/Orchestrator node - LLM-powered brain of the multi-agent system.
    The LLM decides which agent to route to based on the current state and context.
    """
    
    # Supervisor system prompt - LLM acts as the orchestrating brain
    supervisor_prompt = """You are the SUPERVISOR of the AARS (Agentic Alert Resolution System).
You are the orchestrating brain that controls a team of specialized agents.

YOUR TEAM:
- investigator: Queries transaction databases, checks linked accounts, analyzes patterns
- context_gatherer: Retrieves KYC profiles, searches adverse media, checks sanctions
- adjudicator: Makes final resolution decisions based on SOP rules
- conversational: Answers user questions about alerts in a helpful manner

YOUR ROLE:
1. Analyze the current state of the investigation
2. Decide which agent should work next
3. Ensure thorough investigation before making decisions
4. CRITICAL: If you detect CONFIRMED sanctions/terrorist match → Can bypass to immediate BLOCK

ROUTING RULES:
- If mode is "conversation" → Route to "conversational" (user wants to chat)
- If no transaction/pattern analysis done → Route to "investigator"
- If investigator done but no KYC/sanctions check → Route to "context_gatherer"  
- If both investigation and context done, but no decision → Route to "adjudicator"
- If resolution exists → Route to "FINISH"

EMERGENCY BLOCK RULE (CRITICAL):
- If Context Gatherer finds CONFIRMED sanctions match (terrorist, OFAC, UN sanctions)
- AND match confidence is HIGH (>90%)
- You can route directly to "adjudicator" with recommendation to BLOCK_ACCOUNT
- This is for confirmed terrorists, sanctioned entities, or their counterparties

You must respond with ONLY a JSON object:
{
    "next": "<agent_name or FINISH>",
    "reasoning": "<brief explanation of your decision>",
    "emergency_block": true/false (optional - set true if sanctions confirmed)
}

Valid values for "next": investigator, context_gatherer, adjudicator, conversational, FINISH
"""

    def supervisor_node(state: AgentState) -> AgentState:
        print("\n" + "="*80)
        print("🧠 SUPERVISOR (LLM Brain) Activated")
        print("="*80)
        
        # Build context for LLM decision
        mode = state.get("mode", "resolve")
        findings = state.get("findings", [])
        resolution = state.get("resolution", {})
        alert_data = state.get("alert_data", {})
        user_query = state.get("user_query", "")
        
        # Format findings for LLM
        findings_summary = "\n".join(findings) if findings else "No findings yet"
        
        # Create the decision prompt
        decision_prompt = f"""
CURRENT STATE:
- Mode: {mode}
- Alert ID: {alert_data.get('alert_id', 'N/A')}
- Scenario: {alert_data.get('scenario_code', 'N/A')} - {alert_data.get('scenario_name', 'N/A')}
- User Query (if conversation mode): {user_query if mode == 'conversation' else 'N/A'}

INVESTIGATION PROGRESS:
{findings_summary}

RESOLUTION STATUS:
{json.dumps(resolution) if resolution else 'No resolution yet'}

Based on the current state, decide which agent should work next.
Respond with ONLY a JSON object with "next" and "reasoning" fields.
"""

        try:
            # LLM makes the routing decision
            messages = [
                {"role": "system", "content": supervisor_prompt},
                {"role": "user", "content": decision_prompt}
            ]
            
            response = model.invoke(messages)
            response_text = response.content
            
            # Parse LLM response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    decision = json.loads(json_match.group())
                    next_agent = decision.get("next", "FINISH")
                    reasoning = decision.get("reasoning", "No reasoning provided")
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ Failed to parse LLM response, using fallback logic: {e}")
                # Fallback to simple logic if LLM response parsing fails
                if mode == "conversation":
                    next_agent = "conversational"
                    reasoning = "Fallback: Conversation mode detected"
                elif not any("Investigator" in f for f in findings):
                    next_agent = "investigator"
                    reasoning = "Fallback: Investigation needed"
                elif not any("Context Gatherer" in f for f in findings):
                    next_agent = "context_gatherer"
                    reasoning = "Fallback: Context gathering needed"
                elif not resolution:
                    next_agent = "adjudicator"
                    reasoning = "Fallback: Adjudication needed"
                else:
                    next_agent = "FINISH"
                    reasoning = "Fallback: All steps complete"
            
            print(f"🧠 LLM Decision: {next_agent}")
            print(f"💭 Reasoning: {reasoning}")
            
            return {
                "next": next_agent,
                "messages": [AIMessage(content=f"Supervisor reasoning: {reasoning}. Routing to {next_agent}")]
            }
            
        except Exception as e:
            print(f"❌ Supervisor LLM error: {str(e)}")
            # Ultimate fallback
            if mode == "conversation":
                next_agent = "conversational"
            else:
                next_agent = "investigator"
            
            return {
                "next": next_agent,
                "messages": [AIMessage(content=f"Supervisor fallback routing to {next_agent}")]
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
        elif action == "BLOCK_ACCOUNT":
            print(f"\n🚫 CRITICAL ACTION: ACCOUNT BLOCKED!")
            print(f"   ✓ Account {alert_data['subject_id']} IMMEDIATELY FROZEN")
            print(f"   ✓ All transactions HALTED")
            print(f"   ✓ Sanctions compliance team NOTIFIED")
            print(f"   ✓ Regulatory report AUTO-FILED")
            print(f"   ✓ Case escalated to LEGAL DEPARTMENT")
            print(f"   Reason: {resolution['rationale']}")
        
        # Check if IVR is needed (for A-005 Dormant Account scenario)
        if alert_data.get('scenario_code') == 'A-005' and action == "RFI":
            print(f"Action Executed: IVR Call Initiated. Script ID 3 used for simple verification. Awaiting Customer Response...")
        
        print("\n" + "="*80)
        
        return {
            "next": "END",
            "messages": [AIMessage(content=f"AEM executed: {action}")]
        }
    
    return aem_executor_node


def create_conversational_agent(model):
    """
    Create the Conversational Agent - Part of the Supervisor-controlled workflow.
    Handles user queries about alerts using the same tools as investigation agents.
    """
    system_prompt = """You are the AARS Conversational Agent - part of the Agentic Alert Resolution System.

Your role: Answer analyst questions about AML alerts in a conversational, helpful manner.

You have access to the same tools as the investigation agents:
- db_query_history: Query transaction history
- check_linked_accounts: Find related accounts
- check_account_dormancy: Check account activity status
- get_kyc_profile: Get customer KYC data
- search_adverse_media: Search for negative news
- sanctions_lookup: Check sanctions watchlists

Capabilities:
1. Answer questions about alert details, customer profiles, and transaction patterns
2. Explain AML concepts, regulations, and red flags
3. Analyze risks and suggest investigation steps
4. Provide expert opinions on suspicious activity
5. Guide analysts through the investigation process

If the user wants to run a full automated investigation, let them know they can click "🚀 Solve This Alert".

Be conversational, professional, and thorough. You're an AML expert assistant."""

    # Use the same tools as investigation agents
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
        """Conversational agent node - handles user queries under Supervisor control"""
        print("\n" + "="*80)
        print("Conversational Agent Activated (Supervisor-controlled)")
        print("="*80)
        
        alert_data = state["alert_data"]
        user_query = state.get("user_query", "")
        conversation_history = state.get("conversation_history", [])
        
        # Build context from alert and customer data
        customer_info = MOCK_CUSTOMER_DB.get(alert_data.get('subject_id', ''), {})
        
        context = f"""
CURRENT ALERT CONTEXT:
- Alert ID: {alert_data.get('alert_id', 'N/A')}
- Scenario: {alert_data.get('scenario_name', 'N/A')} ({alert_data.get('scenario_code', 'N/A')})
- Customer ID: {alert_data.get('subject_id', 'N/A')}
- Trigger Details: {alert_data.get('trigger_details', 'N/A')}

CUSTOMER PROFILE:
- Name: {customer_info.get('name', 'Unknown')}
- Occupation: {customer_info.get('occupation', 'Unknown')}
- Declared Income: ${customer_info.get('declared_income', 0):,}
- Account Open Date: {customer_info.get('account_open_date', 'Unknown')}
- Risk Rating: {customer_info.get('risk_rating', 'Unknown')}
- KYC Verified: {customer_info.get('kyc_verified', False)}
- Employer: {customer_info.get('employer', 'Unknown')}
"""
        
        # Format conversation history
        history_text = "(No previous messages)"
        if conversation_history:
            formatted = []
            for msg in conversation_history[-6:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")[:200]
                formatted.append(f"{role}: {content}...")
            history_text = "\n".join(formatted)
        
        # Build full query
        full_query = f"""{context}

CONVERSATION HISTORY:
{history_text}

USER QUERY: {user_query}

Respond helpfully to the user's query. Use your tools if needed to gather specific data."""

        try:
            result = agent.invoke({"messages": [HumanMessage(content=full_query)]})
            response = result["messages"][-1].content
            
            print(f"Query: {user_query[:50]}...")
            print(f"Response generated successfully")
            
            # Return new messages to be ADDED to conversation_history via reducer
            # This persists in the checkpoint automatically!
            return {
                "conversation_response": response,
                "conversation_history": [
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": response}
                ],  # These will be appended via operator.add reducer
                "messages": [AIMessage(content="Conversational Agent responded")],
                "next": "FINISH"
            }
        except Exception as e:
            print(f"❌ Conversational Agent error: {str(e)}")
            error_response = f"I encountered an error: {str(e)}. Please try again."
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


def get_conversational_agent():
    """
    Get a standalone conversational agent for use outside the workflow.
    This maintains backward compatibility with app.py
    """
    from config import OPENAI_API_KEY, OPENAI_MODEL
    
    model = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.7,
        api_key=OPENAI_API_KEY
    )
    
    # Create the node function
    node_func = create_conversational_agent(model)
    
    # Wrap it in a simple class for the chat interface
    class ConversationalAgentWrapper:
        def __init__(self, node_func):
            self.node_func = node_func
        
        def chat(self, user_message: str, alert_data: dict, conversation_history: list = None) -> str:
            """Process a user message through the workflow-style agent"""
            # Create a state dict
            state = {
                "alert_data": alert_data,
                "user_query": user_message,
                "conversation_history": conversation_history or [],
                "findings": [],
                "resolution": {},
                "next": "",
                "messages": [],
                "mode": "conversation",
                "conversation_response": ""
            }
            
            # Run the node
            result = self.node_func(state)
            return result.get("conversation_response", "No response generated.")
    
    return ConversationalAgentWrapper(node_func)

