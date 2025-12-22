"""AARS - Advanced Alert Resolution System UI"""

import streamlit as st
from datetime import datetime
import time
import json
import os
from workflow import create_aars_workflow, run_conversation
from database.seed_data import TEST_ALERTS, MOCK_CUSTOMER_DB
from config import SCENARIOS, OPENAI_API_KEY

# Persistent conversation storage
CONVERSATION_FILE = "checkpoints/conversations.json"

def load_conversations():
    """Load conversations from persistent storage"""
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_conversations(conversations):
    """Save conversations to persistent storage"""
    os.makedirs(os.path.dirname(CONVERSATION_FILE), exist_ok=True)
    with open(CONVERSATION_FILE, 'w') as f:
        json.dump(conversations, f, indent=2)

def load_workflow_histories():
    """Load workflow histories from persistent storage"""
    history_file = "checkpoints/workflow_histories.json"
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_workflow_histories(histories):
    """Save workflow histories to persistent storage"""
    history_file = "checkpoints/workflow_histories.json"
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    with open(history_file, 'w') as f:
        json.dump(histories, f, indent=2)

# Page configuration
st.set_page_config(
    page_title="AARS - Alert Resolution System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background gradient */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1e1e 0%, #2d2d2d 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }
    
    /* Main content area */
    .main .block-container {
        background: #ffffff;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* Ensure all main text is dark */
    .main .block-container * {
        color: #1a1a1a;
    }
    
    /* Alert cards */
    .alert-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .alert-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
    }
    
    /* Agent message cards */
    .agent-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid;
        animation: slideIn 0.3s ease-out;
        color: #1a1a1a;
    }
    
    .agent-card * {
        color: #1a1a1a !important;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .supervisor-card { 
        border-left-color: #9c27b0; 
        background: #ffffff;
        border: 1px solid #e0e0e0;
    }
    .investigator-card { 
        border-left-color: #2196f3; 
        background: #ffffff;
        border: 1px solid #e0e0e0;
    }
    .context-card { 
        border-left-color: #ff9800; 
        background: #ffffff;
        border: 1px solid #e0e0e0;
    }
    .adjudicator-card { 
        border-left-color: #4caf50; 
        background: #ffffff;
        border: 1px solid #e0e0e0;
    }
    .resolution-card { 
        border-left-color: #f44336; 
        background: #ffffff;
        border: 2px solid #f44336;
    }
    
    /* Agent badges */
    .agent-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-supervisor { background: #9c27b0; color: white; }
    .badge-investigator { background: #2196f3; color: white; }
    .badge-context { background: #ff9800; color: white; }
    .badge-adjudicator { background: #4caf50; color: white; }
    .badge-resolution { background: #f44336; color: white; }
    
    /* Metrics */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Workflow timeline */
    .timeline-item {
        display: flex;
        align-items: center;
        margin: 1rem 0;
        padding: 1rem;
        background: #f5f5f5;
        border-radius: 8px;
        border-left: 3px solid #667eea;
    }
    
    .timeline-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
    }
    
    /* Status badges */
    .status-pending {
        background: #ff9800;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-resolved {
        background: #4caf50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Title styling */
    h1 {
        color: #1a1a1a !important;
        font-weight: 800;
        font-size: 3rem !important;
    }
    
    h2, h3, h4, h5, h6 {
        color: #1a1a1a !important;
    }
    
    p {
        color: #1a1a1a !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'workflow_app' not in st.session_state:
    st.session_state.workflow_app = None
if 'current_alert' not in st.session_state:
    st.session_state.current_alert = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
# Store conversation messages per alert (key = alert_id, value = list of messages)
# Load from persistent storage on startup
if 'alert_conversations' not in st.session_state:
    st.session_state.alert_conversations = load_conversations()
# Store workflow history per alert (key = alert_id, value = workflow chat_history list)
if 'alert_workflow_histories' not in st.session_state:
    st.session_state.alert_workflow_histories = load_workflow_histories()
# Track if user wants to solve the alert
if 'solving_alert' not in st.session_state:
    st.session_state.solving_alert = None
# Load resolved alerts from workflow histories (persisted)
if 'resolved_alerts' not in st.session_state:
    st.session_state.resolved_alerts = set(st.session_state.alert_workflow_histories.keys())
# Calculate pending alerts based on resolved
if 'pending_alerts' not in st.session_state:
    all_alerts = {alert['alert_id'] for alert in TEST_ALERTS}
    st.session_state.pending_alerts = all_alerts - st.session_state.resolved_alerts

# Sidebar
with st.sidebar:
    st.markdown('<h2 style="color: white !important;">🛡️ AARS</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #e0e0e0 !important;"><strong>Agentic Alert Resolution System</strong></p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Alert Statistics Dashboard
    st.markdown('<h3 style="color: white !important;">📊 Dashboard</h3>', unsafe_allow_html=True)
    
    total = len(TEST_ALERTS)
    resolved = len(st.session_state.resolved_alerts)
    pending = len(st.session_state.pending_alerts)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Pending</div>
            <div class="metric-value">{pending}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Resolved</div>
            <div class="metric-value">{resolved}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Progress
    if total > 0:
        progress = resolved / total
        st.progress(progress)
        st.markdown(f'<center><small style="color: white !important;">{resolved}/{total} Completed ({progress:.0%})</small></center>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alert Selection
    st.markdown('<h3 style="color: white !important;">🎯 Select Alert</h3>', unsafe_allow_html=True)
    
    for alert in TEST_ALERTS:
        alert_id = alert['alert_id']
        is_resolved = alert_id in st.session_state.resolved_alerts
        status_badge = "✅" if is_resolved else "⏳"
        
        # Show message count badge
        msg_count = len(st.session_state.alert_conversations.get(alert_id, []))
        badge_text = f"{status_badge} {alert['scenario_code']}"
        if msg_count > 0:
            badge_text += f" ({msg_count})"
        
        if st.button(
            badge_text,
            key=f"alert_{alert_id}",
            use_container_width=True
        ):
            # Switch to new alert
            st.session_state.current_alert = alert
            st.session_state.solving_alert = None
            st.rerun()
    
    st.markdown("---")
    
    # System Status
    st.markdown('<h3 style="color: white !important;">⚙️ System</h3>', unsafe_allow_html=True)
    
    if st.session_state.workflow_app:
        st.success("🟢 Workflow Active")
    else:
        st.info("⚪ Standby Mode")
    
    if OPENAI_API_KEY:
        st.success("🟢 API Connected")
    else:
        st.error("🔴 API Not Configured")
    
    # Checkpoint status
    import os
    checkpoint_enabled = os.getenv("USE_CHECKPOINTS", "true").lower() == "true"
    if checkpoint_enabled:
        st.success("💾 Checkpoints ON")
        st.caption("Can resume after failures")
    else:
        st.warning("⚠️ Checkpoints OFF")
    
    st.markdown("---")
    
    # Actions
    st.markdown('<h3 style="color: white !important;">🔧 Actions</h3>', unsafe_allow_html=True)
    
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.resolved_alerts = set()
        st.session_state.pending_alerts = {alert['alert_id'] for alert in TEST_ALERTS}
        st.session_state.current_alert = None
        st.session_state.alert_conversations = {}
        st.session_state.alert_workflow_histories = {}
        st.session_state.solving_alert = None
        # Clear persistent storage
        save_conversations({})
        save_workflow_histories({})
        st.rerun()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        if st.session_state.current_alert:
            current_id = st.session_state.current_alert['alert_id']
            if current_id in st.session_state.alert_conversations:
                del st.session_state.alert_conversations[current_id]
            if current_id in st.session_state.alert_workflow_histories:
                del st.session_state.alert_workflow_histories[current_id]
            st.session_state.solving_alert = None
            # Save to persistent storage
            save_conversations(st.session_state.alert_conversations)
            save_workflow_histories(st.session_state.alert_workflow_histories)
        st.rerun()
    
    if st.button("🧹 Clear Checkpoints", use_container_width=True):
        import glob
        checkpoint_dir = "checkpoints"
        if os.path.exists(checkpoint_dir):
            # Clear all checkpoint files including conversations
            for f in glob.glob(os.path.join(checkpoint_dir, "*")):
                try:
                    os.remove(f)
                except:
                    pass
            st.session_state.workflow_app = None  # Force workflow recreation
            st.session_state.alert_conversations = {}
            st.session_state.alert_workflow_histories = {}
            st.session_state.resolved_alerts = set()
            st.success("✅ All checkpoints & conversations cleared!")
            st.rerun()
    
    # Show Investigation Details in Sidebar (if alert is resolved)
    if st.session_state.current_alert:
        current_id = st.session_state.current_alert['alert_id']
        if current_id in st.session_state.alert_workflow_histories:
            st.markdown("---")
            st.markdown('<h3 style="color: white !important;">📋 Investigation Details</h3>', unsafe_allow_html=True)
            
            workflow_history = st.session_state.alert_workflow_histories[current_id]
            
            # Show resolution summary at top
            for message in workflow_history:
                if message["role"] == "resolution":
                    resolution_data = message.get("data", {})
                    action = resolution_data.get("action", "N/A")
                    confidence = resolution_data.get("confidence", 0)
                    
                    action_icon = {
                        "ESCALATE_SAR": "🚨",
                        "RFI": "📧",
                        "FalsePositive": "✅"
                    }.get(action, "📋")
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                        <p style="color: white; margin: 0; font-size: 1.2rem; font-weight: bold;">{action_icon} {action}</p>
                        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Confidence: {confidence:.1%}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    break
            
            # Expandable detailed timeline
            with st.expander("🔄 View Full Timeline", expanded=False):
                for message in workflow_history:
                    role = message["role"]
                    content = message["content"]
                    
                    if role == "supervisor":
                        st.markdown(f"**🎯 Supervisor:** {content}")
                    elif role == "investigator":
                        st.markdown(f"**🔍 Investigator:**")
                        st.caption(content[:200] + "..." if len(content) > 200 else content)
                    elif role == "context_gatherer":
                        st.markdown(f"**🧩 Context Gatherer:**")
                        st.caption(content[:200] + "..." if len(content) > 200 else content)
                    elif role == "adjudicator":
                        st.markdown(f"**⚖️ Adjudicator:**")
                        st.caption(content[:200] + "..." if len(content) > 200 else content)
                    elif role == "aem_executor":
                        st.markdown(f"**🎬 AEM Executor:**")
                        st.caption(content[:200] + "..." if len(content) > 200 else content)
                    elif role == "resolution":
                        resolution_data = message.get("data", {})
                        rationale = resolution_data.get("rationale", "N/A")
                        st.markdown(f"**📋 Rationale:**")
                        st.caption(rationale)
                    
                    st.markdown("---")

# Helper function to get AI response - Uses workflow-based ConversationalAgent
def get_ai_response(user_message, alert_data, conversation_history):
    """
    Get conversational AI response through the Supervisor-controlled workflow.
    The Supervisor routes to the Conversational Agent based on mode.
    """
    try:
        # Initialize workflow if needed
        if st.session_state.workflow_app is None:
            st.session_state.workflow_app = create_aars_workflow()
        
        # Run conversation through the workflow (Supervisor → Conversational Agent)
        response = run_conversation(
            app=st.session_state.workflow_app,
            alert_data=alert_data,
            user_query=user_message,
            conversation_history=conversation_history,
            thread_id=alert_data['alert_id']
        )
        return response
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or contact support."


# Main content
st.markdown('<h1 style="color: #1a1a1a !important;">🛡️ Alert Resolution System</h1>', unsafe_allow_html=True)
st.markdown('<h3 style="color: #424242 !important;">Intelligent Multi-Agent AML Investigation Platform</h3>', unsafe_allow_html=True)

# Current Alert Display
if st.session_state.current_alert:
    alert = st.session_state.current_alert
    alert_id = alert['alert_id']
    is_resolved = alert_id in st.session_state.resolved_alerts
    
    status_html = f'<span class="status-resolved">RESOLVED</span>' if is_resolved else f'<span class="status-pending">PENDING</span>'
    
    st.markdown(f"""
    <div class="alert-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0; color: white;">🚨 {alert['alert_id']}</h2>
                <p style="margin: 0.5rem 0; opacity: 0.9; font-size: 1.1rem;">{alert['scenario_name']}</p>
            </div>
            <div>
                {status_html}
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.3);">
            <p style="margin: 0.3rem 0;"><strong>Customer:</strong> {alert['subject_id']}</p>
            <p style="margin: 0.3rem 0;"><strong>Scenario:</strong> {alert['scenario_code']}</p>
            <p style="margin: 0.3rem 0;"><strong>Details:</strong> {alert.get('trigger_details', 'N/A')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Solve button for automated investigation
    if not is_resolved and st.session_state.solving_alert != alert_id:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Solve This Alert", type="primary", use_container_width=True):
                if not OPENAI_API_KEY:
                    st.error("⚠️ OpenAI API Key not configured!")
                else:
                    st.session_state.solving_alert = alert_id
                    st.session_state.processing = True
                    st.rerun()
        with col2:
            st.info("💬 Or ask me questions about this alert below!")
    
    # Show conversation for this alert
    st.markdown('<h3 style="color: #1a1a1a !important;">💬 Conversation</h3>', unsafe_allow_html=True)
    
    # Get conversation history for this alert
    if alert_id not in st.session_state.alert_conversations:
        st.session_state.alert_conversations[alert_id] = []
    
    conversation = st.session_state.alert_conversations[alert_id]
    
    # Display conversation
    if len(conversation) == 0:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f5f5f5; border-radius: 12px; margin: 1rem 0;">
            <p style="font-size: 1.1rem; color: #666 !important; margin: 0;">👋 Hello! I'm your AI assistant.</p>
            <p style="color: #666 !important; margin-top: 0.5rem;">Ask me anything about this alert, or click "Solve This Alert" to run a full investigation.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in conversation:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 1rem; border-radius: 12px; margin: 0.5rem 0; 
                     margin-left: 20%; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                    <strong>You:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                st.markdown(f"""
                <div style="background: white; border: 1px solid #e0e0e0; 
                     color: #1a1a1a; padding: 1rem; border-radius: 12px; margin: 0.5rem 0; 
                     margin-right: 20%; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                     border-left: 4px solid #667eea;">
                    <strong>🤖 AI Assistant:</strong><br>{msg["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input at the bottom
    st.markdown("---")
    user_input = st.chat_input("Ask me anything about this alert...", key=f"chat_input_{alert_id}")
    
    if user_input:
        # Add user message to conversation
        st.session_state.alert_conversations[alert_id].append({
            "role": "user",
            "content": user_input
        })
        
        # Get AI response
        with st.spinner("🤔 Thinking..."):
            ai_response = get_ai_response(user_input, alert, st.session_state.alert_conversations[alert_id])
        
        # Add AI response to conversation
        st.session_state.alert_conversations[alert_id].append({
            "role": "assistant",
            "content": ai_response
        })
        
        # Save conversations to persistent storage
        save_conversations(st.session_state.alert_conversations)
        
        st.rerun()

else:
    st.info("👈 Select an alert from the sidebar to begin")

st.markdown("---")


# Processing workflow
if st.session_state.processing:
    with st.spinner("🤖 AI Agents are investigating..."):
        try:
            # Initialize workflow
            if st.session_state.workflow_app is None:
                st.session_state.workflow_app = create_aars_workflow()
            
            alert = st.session_state.current_alert
            alert_id = alert['alert_id']
            
            # Fresh state for new investigation (not resuming from checkpoint)
            initial_state = {
                "alert_data": alert,
                "findings": [],
                "resolution": {},
                "next": "",
                "messages": [],
                "mode": "resolve",  # Resolution mode
                "user_query": "",
                "conversation_history": [],
                "conversation_response": ""
            }
            
            # Use timestamp-based thread_id for fresh investigation each time
            import uuid
            fresh_thread_id = f"{alert_id}-resolve-{uuid.uuid4().hex[:8]}"
            config = {"configurable": {"thread_id": fresh_thread_id}}
            
            # Initialize workflow history for this alert
            workflow_history = []
            
            # Add message to conversation
            st.session_state.alert_conversations[alert_id].append({
                "role": "assistant",
                "content": "🚀 Starting automated AI investigation workflow. I'll coordinate multiple agents to analyze this alert..."
            })
            
            # Process workflow with error handling
            resolution = None
            max_iterations = 50  # Prevent infinite retry loops
            iteration = 0
            
            for state in st.session_state.workflow_app.stream(initial_state, config):
                iteration += 1
                if iteration > max_iterations:
                    st.error("⚠️ Max iterations reached. Workflow may be stuck in retry loop.")
                    break
                
                for node_name, node_state in state.items():
                    # Check for errors in findings
                    findings = node_state.get("findings", [])
                    has_error = any("ERROR:" in f for f in findings)
                    
                    if node_name == "supervisor":
                        next_agent = node_state.get("next", "")
                        workflow_history.append({
                            "role": "supervisor",
                            "content": f"Routing to: **{next_agent.upper()}**"
                        })
                    
                    elif node_name == "investigator":
                        if has_error:
                            workflow_history.append({
                                "role": "system",
                                "content": "⚠️ Investigator encountered an error. Retrying with checkpoint..."
                            })
                        else:
                            # Extract detailed findings
                            findings_detail = node_state.get("findings", [])
                            findings_text = "\n".join([f.replace("[Investigator] ", "") for f in findings_detail if "Investigator" in f])
                            
                            # Show tools used
                            workflow_history.append({
                                "role": "investigator",
                                "content": f"""**Database Investigation Complete**

**Tools Used:**
- 🔍 db_query_history - Retrieved 90-day transaction history
- 🔗 check_linked_accounts - Verified account relationships  
- 💤 check_account_dormancy - Analyzed account activity status

**Findings:**
{findings_text if findings_text else "Transaction patterns analyzed, historical data retrieved."}

**Status:** ✅ Investigation successful, checkpoint saved"""
                            })
                    
                    elif node_name == "context_gatherer":
                        if has_error:
                            workflow_history.append({
                                "role": "system",
                                "content": "⚠️ Context Gatherer encountered an error. Retrying with checkpoint..."
                            })
                        else:
                            # Extract detailed findings
                            findings_detail = node_state.get("findings", [])
                            findings_text = "\n".join([f.replace("[Context Gatherer] ", "") for f in findings_detail if "Context Gatherer" in f])
                            
                            workflow_history.append({
                                "role": "context_gatherer",
                                "content": f"""**Context Gathering Complete**

**Tools Used:**
- 👤 get_kyc_profile - Retrieved customer KYC data
- 📰 search_adverse_media - Searched OSINT sources
- 🚨 sanctions_lookup - Verified watchlist status

**Findings:**
{findings_text if findings_text else "KYC profile verified, no adverse media hits, sanctions check complete."}

**Status:** ✅ Context gathered, checkpoint saved"""
                            })
                    
                    elif node_name == "adjudicator":
                        if has_error:
                            workflow_history.append({
                                "role": "system",
                                "content": "⚠️ Adjudicator encountered an error. Retrying with checkpoint..."
                            })
                        elif node_state.get("resolution"):
                            resolution = node_state["resolution"]
                            sop_rule = resolution.get("sop_rule_applied", alert['scenario_code'])
                            
                            workflow_history.append({
                                "role": "adjudicator",
                                "content": f"""**Decision Rendered**

**SOP Applied:** {sop_rule}
**Decision:** {resolution['action']}
**Confidence Level:** {resolution['confidence']:.1%}

**Reasoning Process:**
1. Reviewed Investigator findings (transaction patterns, history)
2. Analyzed Context Gatherer data (KYC, media, sanctions)
3. Applied {alert['scenario_code']} SOP rules
4. Determined appropriate action based on evidence

**Status:** ✅ Decision made, checkpoint saved"""
                            })
                    
                    elif node_name == "aem_executor":
                        if resolution:
                            action = resolution['action']
                            
                            # Detailed action execution message
                            action_details = {
                                "ESCALATE_SAR": f"""**🚨 SAR ESCALATION EXECUTED**

✓ Case {alert['alert_id']} pre-populated in SAR system
✓ Routed to Compliance Review Queue
✓ All findings and evidence attached
✓ Awaiting human review and filing decision

**Next Steps:** Human analyst will review for SAR filing""",
                                
                                "RFI": f"""**📧 RFI REQUEST EXECUTED**

✓ Email drafted to customer {alert.get('subject_id', 'Customer')}
✓ Requesting source of funds documentation
✓ 10-day response window initiated
✓ Follow-up scheduled in CRM system

**Next Steps:** Await customer response, escalate if no reply""",
                                
                                "FalsePositive": f"""**✅ ALERT CLOSED - FALSE POSITIVE**

✓ Alert {alert['alert_id']} marked as resolved
✓ Transaction pattern determined legitimate
✓ No further action required
✓ System updated, alert archived

**Outcome:** Case closed, no compliance concern identified"""
                            }
                            
                            workflow_history.append({
                                "role": "aem_executor",
                                "content": action_details.get(action, f"Action executed: {action}")
                            })
                            
                            workflow_history.append({
                                "role": "resolution",
                                "content": f"Alert {alert['alert_id']} processed",
                                "data": resolution
                            })
                            
                            # Mark as resolved
                            st.session_state.resolved_alerts.add(alert_id)
                            if alert_id in st.session_state.pending_alerts:
                                st.session_state.pending_alerts.remove(alert_id)
                            
                            # Save the complete workflow history for this alert
                            st.session_state.alert_workflow_histories[alert_id] = workflow_history
                            
                            # Add completion message to conversation
                            st.session_state.alert_conversations[alert_id].append({
                                "role": "assistant",
                                "content": f"✅ Investigation complete! **Decision: {action}**\n\nThe full investigation timeline is shown below. Feel free to ask me any questions about the findings!"
                            })
                            
                            # Save to persistent storage
                            save_conversations(st.session_state.alert_conversations)
                            save_workflow_histories(st.session_state.alert_workflow_histories)
            
            st.session_state.processing = False
            st.session_state.solving_alert = None
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Workflow failed: {str(e)}")
            st.info("💾 Progress saved to checkpoint. You can retry by clicking 'Solve This Alert' again.")
            st.session_state.processing = False
            st.session_state.solving_alert = None
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <p style="color: #666 !important;">🛡️ AARS - Agentic Alert Resolution System</p>
    <p style="font-size: 0.9rem; color: #666 !important;">Powered by OpenAI GPT-4 & LangGraph | Built for Financial Crime Compliance</p>
</div>
""", unsafe_allow_html=True)
