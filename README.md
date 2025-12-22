# 🛡️ AARS - Agentic Alert Resolution System

An intelligent multi-agent AML (Anti-Money Laundering) investigation platform powered by OpenAI GPT-4 and LangGraph. Features a conversational ChatGPT-like interface for investigating financial crime alerts.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Enabled-green.svg)

---

## ✨ Features

### 💬 Conversational AI Interface
- **ChatGPT-like experience** - Ask questions about any alert naturally
- **Per-alert conversations** - Each alert maintains its own chat history
- **Context-aware responses** - AI has full knowledge of customer data, transactions, and alert details

### 🤖 Multi-Agent Investigation Workflow (LLM-Powered Orchestration)
- **Supervisor Agent (LLM Brain)** - GPT-powered orchestrator that decides which agent to invoke next
- **Investigator Agent** - Analyzes transaction patterns and history
- **Context Gatherer Agent** - Retrieves KYC data, sanctions, and adverse media
- **Adjudicator Agent** - Makes final decisions based on SOP rules
- **AEM Executor** - Executes the resolution action
- **Conversational Agent** - Handles user queries (routed by Supervisor, uses same tools)

> **True Agentic AI**: The Supervisor uses LLM reasoning (not if-else logic) to decide routing based on investigation state, making intelligent orchestration decisions.

### 🎯 5 Pre-configured Alert Scenarios
| Code | Scenario | Description |
|------|----------|-------------|
| A-001 | Velocity Spike | 5+ transactions > $5k within 48 hours (Layering) |
| A-002 | Structuring | 3 cash deposits between $9k-$9.9k in 7 days |
| A-003 | KYC Inconsistency | Transaction doesn't match customer profile |
| A-004 | Sanctions Hit | Confirmed terrorist/sanctioned entity → BLOCK_ACCOUNT |
| A-005 | Dormant Reactivation | Dormant account with sudden large activity |

### 📊 Resolution Actions
- **ESCALATE_SAR** - Escalate for Suspicious Activity Report filing
- **RFI** - Request for Information from customer
- **FalsePositive** - Close alert as false positive
- **BLOCK_ACCOUNT** - ⛔ Immediate account freeze for confirmed sanctions/terrorist matches

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- OpenAI API Key

### 2. Installation

```bash
# Clone the repository
cd Alert_Resolution_System

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key-here
USE_CHECKPOINTS=true
```

### 4. Seed the Database

```bash
python database/seed_data.py
```

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 🎮 How to Use

### Investigating Alerts

1. **Select an Alert** - Click any alert from the sidebar (⏳ pending, ✅ resolved)

2. **Ask Questions** - Chat with the AI about the alert:
   - "What's suspicious about this alert?"
   - "Tell me about the customer's background"
   - "What are the risk factors here?"
   - "Should this be escalated?"

3. **Solve the Alert** - Click "🚀 Solve This Alert" to run the full AI investigation

4. **Review Results** - Investigation details appear in the sidebar under "📋 Investigation Details"

5. **Continue Chatting** - Ask follow-up questions about the resolution

---

## 📁 Project Structure

```
Alert_Resolution_System/
├── app.py                 # Streamlit Conversational UI
├── workflow.py            # LangGraph workflow with checkpointing
├── agents.py              # All agents (including ConversationalAgent)
├── tools.py               # Agent tools (DB queries, sanctions, KYC)
├── state.py               # AgentState definition
├── config.py              # Configuration settings
├── scenarios.py           # Alert scenario definitions
├── checkpoint_manager.py  # Checkpoint utilities
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   ├── connection.py      # Database connection
│   └── seed_data.py       # Test data seeding
├── checkpoints/           # Workflow checkpoint storage
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── README.md
```

---

## 🗄️ Database

The system uses SQLite databases:

| Database | Purpose |
|----------|---------|
| `aars_database.db` | Business data (customers, transactions, alerts) |
| `checkpoints/aars_checkpoints.db` | Workflow state checkpoints |

### Reseed Database

```bash
python database/seed_data.py
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `USE_CHECKPOINTS` | Enable workflow checkpointing | `true` |
| `CHECKPOINT_DB` | Checkpoint database path | `checkpoints/aars_checkpoints.db` |

### Model Settings (config.py)

```python
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-4", "gpt-3.5-turbo"
OPENAI_TEMPERATURE = 0.1
```

---

## 🔧 Agent Tools

| Tool | Agent | Description |
|------|-------|-------------|
| `db_query_history` | Investigator | Query 90-day transaction history |
| `check_linked_accounts` | Investigator | Find related accounts |
| `check_account_dormancy` | Investigator | Analyze account activity status |
| `get_kyc_profile` | Context Gatherer | Retrieve customer KYC data |
| `search_adverse_media` | Context Gatherer | Search OSINT sources |
| `sanctions_lookup` | Context Gatherer | Check sanctions watchlists |

---

## 🏗️ Architecture

```
                    ┌─────────────────────┐
                    │  🧠 SUPERVISOR      │
                    │   (LLM Brain)       │
                    │                     │
                    │ "Which agent next?" │
                    │  ↓ LLM Reasoning ↓  │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
  ┌───────────┐         ┌───────────┐          ┌───────────┐
  │INVESTIGATOR│        │ CONTEXT   │          │ADJUDICATOR│
  │  (Tools)  │         │ GATHERER  │          │  (SOP)    │
  └─────┬─────┘         └─────┬─────┘          └─────┬─────┘
        │                     │                      │
        └─────────────────────┼──────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ CONVERSATIONAL      │
                    │    AGENT            │
                    │ (Same 6 Tools)      │
                    └─────────────────────┘
```

**LLM-Powered Orchestration:**
- Supervisor uses **GPT reasoning** to analyze state and decide next agent
- Not hardcoded if-else logic - true agentic AI decision making
- Supervisor provides reasoning for each routing decision

**Two Modes - One LLM Brain:**
- **Resolve Mode**: Supervisor reasons → Investigator → Context Gatherer → Adjudicator → AEM
- **Conversation Mode**: Supervisor reasons → Conversational Agent

---

## 💾 Checkpointing

The system uses LangGraph's `SqliteSaver` for fault-tolerant workflow execution:

- **Auto-save** after each agent step
- **Resume capability** if workflow fails mid-execution
- **Thread-based** - Each alert maintains its own checkpoint thread

---

## 🛠️ Development

### Run CLI Mode

```bash
python run.py
```

### Disable Checkpoints (for debugging)

```bash
USE_CHECKPOINTS=false streamlit run app.py
```

---

## 📝 License

MIT License

---

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [OpenAI GPT-4](https://openai.com)
- UI by [Streamlit](https://streamlit.io)

---

**Made with ❤️ for Financial Crime Compliance**
