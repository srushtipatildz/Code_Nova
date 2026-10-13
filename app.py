import streamlit as st
import json
import time
import uuid
import os
from datetime import datetime, timezone

import db
import tools
import agent

st.set_page_config(
    page_title="MayI — Consent Layer for Local AI Agents",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and demo workspace
db.init_db()
tools.ensure_workspace()

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = f"sess_{str(uuid.uuid4())[:8]}"
if "allowed_tools" not in st.session_state:
    st.session_state.allowed_tools = ["read_notes", "save_notes", "list_notes", "scan_security"]
if "blocked_tools" not in st.session_state:
    st.session_state.blocked_tools = ["delete_notes"]
if "duration_minutes" not in st.session_state:
    st.session_state.duration_minutes = 10
if "simulation_mode" not in st.session_state:
    st.session_state.simulation_mode = False
if "pending_proposals" not in st.session_state:
    st.session_state.pending_proposals = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_data" not in st.session_state:
    st.session_state.session_data = db.create_session(
        session_id=st.session_state.session_id,
        duration_minutes=st.session_state.duration_minutes,
        allowed_tools=st.session_state.allowed_tools,
        blocked_tools=st.session_state.blocked_tools
    )

# Refresh session from DB
current_session = db.get_session(st.session_state.session_id)
if not current_session:
    current_session = db.create_session(
        session_id=st.session_state.session_id,
        duration_minutes=st.session_state.duration_minutes,
        allowed_tools=st.session_state.allowed_tools,
        blocked_tools=st.session_state.blocked_tools
    )
st.session_state.session_data = current_session

# ---------------------------------------------------------
# Custom Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #1E293B;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .proposal-card {
        background-color: #F8FAFC;
        border: 2px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .badge-approved {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-blocked {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-pending {
        background-color: #FEF08A;
        color: #713F12;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: System Status & Security Controls
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ **MayI Consent Layer**")
    st.caption("Human-in-the-loop control for local open-source AI")

    # Ollama Connectivity Status
    ollama_info = agent.check_ollama_status()
    st.divider()
    st.subheader("🤖 Local AI Engine")
    
    if ollama_info["connected"]:
        st.success("🟢 Ollama Connected (`localhost:11434`)")
        available_models = ollama_info["models"] or ["qwen2.5:3b"]
        selected_model = st.selectbox(
            "Active Model:",
            available_models,
            index=0 if "qwen2.5:3b" not in available_models else available_models.index("qwen2.5:3b")
        )
    else:
        st.warning("⚠️ Ollama Offline on port 11434")
        st.info("Run `ollama run qwen2.5:3b` in your terminal for real local inference.")
        use_sim = st.toggle("Enable Simulation Fallback", value=True, help="Simulates Qwen2.5 tool planning when Ollama is offline.")
        st.session_state.simulation_mode = use_sim
        selected_model = "qwen2.5:3b (Simulated)"

    st.divider()

    # Session Status & Expiry Timer
    st.subheader("⏱️ Session Scope & Expiry")
    sess_status = current_session["status"]
    
    if sess_status == "ACTIVE":
        exp_dt = datetime.fromisoformat(current_session["expires_at"])
        remaining_secs = int(exp_dt.timestamp() - datetime.now(timezone.utc).timestamp())
        if remaining_secs > 0:
            mins, secs = divmod(remaining_secs, 60)
            st.metric("Time Remaining", f"{mins:02d}:{secs:02d}", delta="Active Window", delta_color="normal")
        else:
            st.error("⏰ Session Expired")
    elif sess_status == "STOPPED":
        st.error("🛑 Session Terminated (STOP Switch)")
    else:
        st.warning("⏰ Session Expired")

    st.caption(f"Session ID: `{current_session['session_id']}`")

    # Granular Permissions Configuration
    with st.expander("⚙️ Configure Permissions", expanded=False):
        all_available_tools = list(tools.TOOL_REGISTRY.keys())
        new_allowed = st.multiselect(
            "Allowed Tools:",
            options=all_available_tools,
            default=[t for t in st.session_state.allowed_tools if t in all_available_tools]
        )
        new_blocked = st.multiselect(
            "Blocked Tools (Hard Policy):",
            options=all_available_tools,
            default=[t for t in st.session_state.blocked_tools if t in all_available_tools]
        )
        new_duration = st.slider("Duration (minutes):", min_value=1, max_value=60, value=st.session_state.duration_minutes)

        if st.button("Apply & Start New Session", use_container_width=True):
            new_id = f"sess_{str(uuid.uuid4())[:8]}"
            st.session_state.session_id = new_id
            st.session_state.allowed_tools = new_allowed
            st.session_state.blocked_tools = new_blocked
            st.session_state.duration_minutes = new_duration
            st.session_state.pending_proposals = []
            st.session_state.chat_history = []
            st.session_state.session_data = db.create_session(
                session_id=new_id,
                duration_minutes=new_duration,
                allowed_tools=new_allowed,
                blocked_tools=new_blocked
            )
            st.rerun()

    st.divider()

    # Emergency Kill Switch
    st.subheader("🚨 Emergency Kill Switch")
    if st.button("🔴 STOP ALL (Instant Revoke)", use_container_width=True, type="primary"):
        db.stop_session(st.session_state.session_id)
        st.session_state.pending_proposals = []
        st.toast("🛑 EMERGENCY STOP TRIGGERED. All agent permissions revoked!", icon="🚨")
        st.rerun()

    st.divider()

    # Downloadable Receipts
    st.subheader("📥 Export Audit Receipt")
    receipt_json = db.export_receipt_json(st.session_state.session_id)
    receipt_md = db.export_receipt_markdown(st.session_state.session_id)

    st.download_button(
        label="Download JSON Receipt",
        data=receipt_json,
        file_name=f"mayi_receipt_{st.session_state.session_id}.json",
        mime="application/json",
        use_container_width=True
    )
    st.download_button(
        label="Download Markdown Receipt",
        data=receipt_md,
        file_name=f"mayi_receipt_{st.session_state.session_id}.md",
        mime="text/markdown",
        use_container_width=True
    )

# ---------------------------------------------------------
# Main UI Layout
# ---------------------------------------------------------
st.markdown('<div class="main-header">MayI 🛡️ — Agent Consent Layer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'An offline, zero-trust consent architecture for local AI agents (powered by <b>Qwen2.5 3B</b> via <b>Ollama</b>). '
    'The agent cannot act without your explicit authorization. '
    '<i>Inspired by the idea of agent consent layers, such as My Agent Ohana.</i>'
    '</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["💬 Agent & Consent Gate", "🧾 Live Audit Trail", "📁 Safe Workspace Files"])

# ---------------------------------------------------------
# TAB 1: Agent & Consent Gate
# ---------------------------------------------------------
with tab1:
    col_input, col_status = st.columns([3, 1])

    with col_input:
        user_prompt = st.text_input(
            "Give the agent a task:",
            placeholder="e.g. Read my meeting notes, summarize the goals, and save it to summary.txt",
            disabled=(current_session["status"] != "ACTIVE")
        )

    with col_status:
        st.write("")
        st.write("")
        submit_btn = st.button("Submit Task", type="primary", use_container_width=True, disabled=(current_session["status"] != "ACTIVE"))

    # Quick demo buttons
    st.caption("Quick Demo Scenarios:")
    demo_cols = st.columns(3)
    if demo_cols[0].button("📝 1. Summarize Notes (Allowed Flow)", use_container_width=True):
        user_prompt = "Read meeting_notes.txt, summarize key decisions, and save it to summary.txt"
        submit_btn = True
    if demo_cols[1].button("🛑 2. Delete File (Blocked Flow)", use_container_width=True):
        user_prompt = "Permanently delete old_debug_log.txt from the workspace"
        submit_btn = True
    if demo_cols[2].button("🔍 3. Security Scan (Repo Scan Flow)", use_container_width=True):
        user_prompt = "Run crops-scan to check for leaked secrets or keys"
        submit_btn = True

    # Process Task submission
    if submit_btn and user_prompt:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        
        # Check session viability
        if current_session["status"] != "ACTIVE":
            st.error(f"Cannot process task: Session is {current_session['status']}.")
        else:
            with st.spinner("Qwen2.5 3B is reasoning and deciding which tools to call..."):
                proposals = []
                
                # Check if Ollama is connected or simulation mode
                if ollama_info["connected"] and not st.session_state.simulation_mode:
                    resp = agent.call_ollama_agent(user_prompt, conversation_history=[], model=selected_model)
                    if resp.get("success"):
                        tool_calls = resp.get("tool_calls", [])
                        if not tool_calls:
                            st.session_state.chat_history.append({"role": "assistant", "content": resp.get("content", "Task processed with no tool calls.")})
                        for tc in tool_calls:
                            func = tc.get("function", {})
                            name = func.get("name", "")
                            try:
                                args = json.loads(func.get("arguments", "{}")) if isinstance(func.get("arguments"), str) else func.get("arguments", {})
                            except Exception:
                                args = {}
                            proposals.append({
                                "tool_name": name,
                                "tool_args": args,
                                "rationale": f"The model selected '{name}' to satisfy user prompt: '{user_prompt}'."
                            })
                    else:
                        st.error(resp.get("error", "Error contacting Ollama"))
                else:
                    # Simulated Intelligent Decision Engine (Qwen2.5 Fallback)
                    p_lower = user_prompt.lower()
                    if "delete" in p_lower:
                        proposals.append({
                            "tool_name": "delete_notes",
                            "tool_args": {"filename": "old_debug_log.txt"},
                            "rationale": "The user requested cleanup, so I need to remove old_debug_log.txt from the workspace."
                        })
                    elif "scan" in p_lower or "security" in p_lower or "secret" in p_lower:
                        proposals.append({
                            "tool_name": "scan_security",
                            "tool_args": {"target": "workspace"},
                            "rationale": "Executing crops-scan security audit to discover potential credential leaks."
                        })
                    elif "summarize" in p_lower or "meeting" in p_lower or "read" in p_lower:
                        proposals.append({
                            "tool_name": "read_notes",
                            "tool_args": {"filename": "meeting_notes.txt"},
                            "rationale": "I must inspect the contents of meeting_notes.txt before producing a summary."
                        })
                        proposals.append({
                            "tool_name": "save_notes",
                            "tool_args": {
                                "filename": "summary.txt",
                                "content": "Hackathon Summary: Aim for Best Open-Source AI Project. Qwen2.5 3B running offline via Ollama. 100% local consent layer."
                            },
                            "rationale": "After reading the notes, I need to persist the extracted summary to summary.txt."
                        })
                    elif "alert" in p_lower or "notify" in p_lower:
                        proposals.append({
                            "tool_name": "send_alert",
                            "tool_args": {"message": "Hackathon demo is ready and operating under MayI consent layer."},
                            "rationale": "User requested to alert the team regarding the demo status."
                        })
                    else:
                        proposals.append({
                            "tool_name": "list_notes",
                            "tool_args": {},
                            "rationale": "I need to inspect available workspace files to fulfill the request."
                        })

                # Evaluate proposals through MayI Consent Layer
                for p in proposals:
                    eval_res = agent.evaluate_consent_policy(
                        session_id=st.session_state.session_id,
                        tool_name=p["tool_name"],
                        tool_args=p["tool_args"],
                        rationale=p["rationale"]
                    )
                    p["eval"] = eval_res
                    if eval_res["decision"] == "NEEDS_APPROVAL":
                        st.session_state.pending_proposals.append(p)
                    elif eval_res["decision"] == "BLOCKED":
                        st.toast(f"🛑 Auto-Blocked: {p['tool_name']}", icon="🛑")

    st.write("---")

    # -----------------------------------------------------
    # HUMAN-IN-THE-LOOP APPROVAL QUEUE
    # -----------------------------------------------------
    st.subheader("🔔 Human Consent Approval Queue")

    if not st.session_state.pending_proposals:
        st.info("No actions currently pending approval. Give the agent a task above!")
    else:
        st.markdown(f"**{len(st.session_state.pending_proposals)} Action Proposal(s) awaiting your decision:**")
        
        # Render each proposal card
        for idx, prop in enumerate(list(st.session_state.pending_proposals)):
            eval_info = prop.get("eval", {})
            action_id = eval_info.get("action_id")
            
            with st.container():
                st.markdown(f"""
                <div class="proposal-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 1.15rem; font-weight: 700; color: #1E293B;">
                            🔧 Proposed Tool: <code>{prop['tool_name']}</code>
                        </span>
                        <span class="badge-pending">⏳ Awaiting Consent</span>
                    </div>
                    <p style="margin: 4px 0; color: #334155;"><b>Agent's Stated Rationale:</b> <i>"{prop['rationale']}"</i></p>
                    <p style="margin: 4px 0; color: #475569;"><b>Target Arguments:</b> <code>{json.dumps(prop['tool_args'])}</code></p>
                </div>
                """, unsafe_allow_html=True)

                col_approve, col_deny, _ = st.columns([1, 1, 3])
                
                if col_approve.button(f"✅ Approve Action #{action_id}", key=f"app_{action_id}_{idx}", type="primary"):
                    # Check again if session hasn't expired or stopped in the interim
                    curr = db.get_session(st.session_state.session_id)
                    if curr["status"] != "ACTIVE":
                        st.error(f"Cannot execute: Session is {curr['status']}!")
                    else:
                        # Execute the tool
                        exec_result = tools.execute_tool(prop["tool_name"], prop["tool_args"])
                        db.update_action_status(action_id, status="EXECUTED", result=exec_result)
                        st.session_state.pending_proposals.remove(prop)
                        st.success(f"Executed `{prop['tool_name']}`: {exec_result}")
                        st.rerun()

                if col_deny.button(f"❌ Deny Action #{action_id}", key=f"deny_{action_id}_{idx}"):
                    db.update_action_status(action_id, status="DENIED_BY_USER", result="Rejected by human operator.")
                    st.session_state.pending_proposals.remove(prop)
                    st.warning(f"Action `{prop['tool_name']}` denied by you.")
                    st.rerun()

# ---------------------------------------------------------
# TAB 2: Live Audit Receipt
# ---------------------------------------------------------
with tab2:
    st.subheader(f"🧾 Audit Receipt Ledger for Session `{st.session_state.session_id}`")
    
    actions = db.get_actions(st.session_state.session_id)
    if not actions:
        st.write("No actions logged yet in this session.")
    else:
        # Metrics summary
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Proposed", len(actions))
        col2.metric("Executed (Approved)", sum(1 for a in actions if a["status"] == "EXECUTED"))
        col3.metric("Denied by User", sum(1 for a in actions if a["status"] == "DENIED_BY_USER"))
        col4.metric("Blocked by Policy", sum(1 for a in actions if "BLOCK" in a["status"]))
        
        st.write("---")
        
        for a in reversed(actions):
            status = a["status"]
            if status == "EXECUTED":
                icon = "🟢"
                badge_class = "badge-approved"
            elif "BLOCK" in status:
                icon = "🛑"
                badge_class = "badge-blocked"
            elif status == "DENIED_BY_USER":
                icon = "❌"
                badge_class = "badge-blocked"
            else:
                icon = "⏳"
                badge_class = "badge-pending"

            with st.expander(f"{icon} {a['timestamp']} — Tool: {a['tool_name']} [{status}]", expanded=(status in ["EXECUTED", "AUTO_BLOCKED_POLICY"])):
                st.markdown(f"**Status:** <span class='{badge_class}'>{status}</span>", unsafe_allow_html=True)
                st.markdown(f"**Agent Rationale:** _{a['rationale']}_")
                st.markdown(f"**Arguments:** `{json.dumps(a['tool_args'])}`")
                if a["result"]:
                    st.markdown(f"**Result / Output:** `{a['result']}`")

# ---------------------------------------------------------
# TAB 3: Safe Workspace Files
# ---------------------------------------------------------
with tab3:
    st.subheader("📁 Safe Sandbox Workspace")
    st.caption(f"Path: `{tools.WORKSPACE_DIR}`")

    w_files = os.listdir(tools.WORKSPACE_DIR) if os.path.exists(tools.WORKSPACE_DIR) else []
    
    if not w_files:
        st.info("Workspace is empty.")
    else:
        selected_file = st.selectbox("Inspect workspace file:", w_files)
        if selected_file:
            fpath = os.path.join(tools.WORKSPACE_DIR, selected_file)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    file_content = f.read()
                st.text_area(f"Contents of {selected_file}:", value=file_content, height=200, disabled=True)
            except Exception as e:
                st.error(f"Error reading file: {e}")

    if st.button("🔄 Reset Workspace Demo Files"):
        tools.ensure_workspace()
        st.success("Demo workspace restored!")
        st.rerun()
