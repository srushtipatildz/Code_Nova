import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from tools import TOOL_DEFINITIONS, execute_tool
import db

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = """You are MayI Agent, an autonomous assistant operating under a strict Human Consent Layer.
You are running locally on Qwen2.5 3B.
Rules you must strictly follow:
1. You have access to specific tools: read_notes, save_notes, list_notes, delete_notes, scan_security, send_alert.
2. For EVERY tool you decide to use, you must clearly explain your RATIONALE (why you need this tool and what you intend to do).
3. You do NOT have blanket permission. Every action you propose will be audited, policy-checked, and presented to the human for approval.
4. When calling a tool, provide clear and concise arguments.
"""

def check_ollama_status(base_url: str = OLLAMA_BASE_URL) -> Dict[str, Any]:
    """Checks whether the Ollama local API is accessible and lists available models."""
    url = f"{base_url}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                models_info = body.get("models", [])
                model_names = [m.get("name", "") for m in models_info]
                return {
                    "connected": True,
                    "models": model_names,
                    "has_default": any(DEFAULT_MODEL in name for name in model_names),
                    "error": None
                }
    except Exception as e:
        return {
            "connected": False,
            "models": [],
            "has_default": False,
            "error": str(e)
        }
    return {
        "connected": False,
        "models": [],
        "has_default": False,
        "error": "Unexpected response"
    }

def call_ollama_agent(
    prompt: str,
    conversation_history: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    base_url: str = OLLAMA_BASE_URL
) -> Dict[str, Any]:
    """
    Calls local Ollama Qwen2.5 model with tool definitions.
    Returns parsed message containing either a tool proposal or final response.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    url = f"{base_url}/api/chat"
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            message = data.get("message", {})
            tool_calls = message.get("tool_calls", [])
            content = message.get("content", "")

            return {
                "success": True,
                "content": content,
                "tool_calls": tool_calls
            }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": f"Ollama HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to connect to Ollama: {str(e)}"
        }

def evaluate_consent_policy(
    session_id: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    rationale: str
) -> Dict[str, Any]:
    """
    The MayI Consent Layer verification engine:
    1. Validates session state (Active vs Expired vs Stopped).
    2. Validates against explicit BLOCKED list.
    3. Validates against ALLOWED list.
    4. Queues for Human-In-The-Loop approval if allowed.
    """
    session = db.get_session(session_id)
    if not session:
        return {
            "decision": "DENIED",
            "status": "NO_SESSION",
            "message": "Invalid or missing session."
        }
    
    # 1. Kill-Switch Check
    if session["status"] == "STOPPED":
        db.log_action(
            session_id=session_id,
            tool_name=tool_name,
            tool_args=tool_args,
            rationale=rationale,
            status="AUTO_BLOCKED_POLICY",
            result="Blocked: Emergency kill switch was triggered."
        )
        return {
            "decision": "BLOCKED",
            "status": "KILLED_BY_STOP_SWITCH",
            "message": "Action blocked: The session was halted by the Emergency Stop button."
        }

    # 2. Expiry Window Check
    if session["status"] == "EXPIRED":
        db.log_action(
            session_id=session_id,
            tool_name=tool_name,
            tool_args=tool_args,
            rationale=rationale,
            status="AUTO_BLOCKED_EXPIRED",
            result="Blocked: Session duration window expired."
        )
        return {
            "decision": "BLOCKED",
            "status": "AUTO_BLOCKED_EXPIRED",
            "message": "Action blocked: Session permission time window has expired."
        }

    # 3. Explicit Blocklist Check
    if tool_name in session["blocked_tools"]:
        action_id = db.log_action(
            session_id=session_id,
            tool_name=tool_name,
            tool_args=tool_args,
            rationale=rationale,
            status="AUTO_BLOCKED_POLICY",
            result=f"Blocked by policy: '{tool_name}' is on the blocked list."
        )
        return {
            "decision": "BLOCKED",
            "status": "AUTO_BLOCKED_POLICY",
            "action_id": action_id,
            "message": f"Action automatically blocked: '{tool_name}' is prohibited by your session policy."
        }

    # 4. Scope Whitelist Check
    if tool_name not in session["allowed_tools"]:
        action_id = db.log_action(
            session_id=session_id,
            tool_name=tool_name,
            tool_args=tool_args,
            rationale=rationale,
            status="AUTO_BLOCKED_POLICY",
            result=f"Blocked: '{tool_name}' is not in the allowed list."
        )
        return {
            "decision": "BLOCKED",
            "status": "AUTO_BLOCKED_POLICY",
            "action_id": action_id,
            "message": f"Action blocked: '{tool_name}' is not granted in the allowed permissions."
        }

    # 5. Passed Policy -> Now requires explicit Human Approval
    action_id = db.log_action(
        session_id=session_id,
        tool_name=tool_name,
        tool_args=tool_args,
        rationale=rationale,
        status="PROPOSED",
        result=""
    )
    return {
        "decision": "NEEDS_APPROVAL",
        "status": "PROPOSED",
        "action_id": action_id,
        "message": "Action permitted by policy scope. Awaiting your approval."
    }
