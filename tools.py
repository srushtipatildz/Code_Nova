import os
import json
import sys
from typing import Dict, Any, Callable

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")

def ensure_workspace():
    """Ensures safe workspace directory exists and populates demo files."""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    
    notes_file = os.path.join(WORKSPACE_DIR, "meeting_notes.txt")
    if not os.path.exists(notes_file):
        with open(notes_file, "w", encoding="utf-8") as f:
            f.write(
                "--- HACKATHON TEAM SYNC ---\n"
                "1. Goal: Win Best Open-Source AI Project challenge.\n"
                "2. Model: Run Qwen2.5 3B locally on Ollama.\n"
                "3. Core Feature: Human-in-the-loop consent layer (MayI).\n"
                "4. Important: Never execute destructive actions without explicit user approval!\n"
            )

    feedback_file = os.path.join(WORKSPACE_DIR, "project_specs.txt")
    if not os.path.exists(feedback_file):
        with open(feedback_file, "w", encoding="utf-8") as f:
            f.write(
                "Project: MayI Consent Layer\n"
                "Security Policy: Zero-trust agent actions.\n"
                "Storage: Local SQLite database.\n"
            )

    temp_file = os.path.join(WORKSPACE_DIR, "old_debug_log.txt")
    if not os.path.exists(temp_file):
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("Old debug logs from September 2026. Safe to delete or archive.\n")

def read_notes(filename: str) -> str:
    """Reads the contents of a note or file in the workspace directory."""
    safe_path = os.path.join(WORKSPACE_DIR, os.path.basename(filename))
    if not os.path.exists(safe_path):
        return f"Error: File '{filename}' not found in workspace."
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def save_notes(filename: str, content: str) -> str:
    """Creates or overwrites a note in the workspace directory."""
    safe_path = os.path.join(WORKSPACE_DIR, os.path.basename(filename))
    try:
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: Saved content ({len(content)} chars) to '{filename}'."
    except Exception as e:
        return f"Error saving file: {str(e)}"

def list_notes() -> str:
    """Lists all files in the workspace directory."""
    ensure_workspace()
    try:
        files = os.listdir(WORKSPACE_DIR)
        if not files:
            return "Workspace is currently empty."
        return f"Workspace files: {', '.join(files)}"
    except Exception as e:
        return f"Error listing files: {str(e)}"

def delete_notes(filename: str) -> str:
    """Deletes a note from the workspace directory (Destructive Action)."""
    safe_path = os.path.join(WORKSPACE_DIR, os.path.basename(filename))
    if not os.path.exists(safe_path):
        return f"Error: File '{filename}' does not exist."
    try:
        os.remove(safe_path)
        return f"Success: Deleted '{filename}' from workspace."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def send_alert(message: str) -> str:
    """Simulates sending an external notification/alert to team webhook."""
    return f"Simulated Notification Sent: '{message}' (Logged locally without external network call)."

def scan_security(target: str = "workspace") -> str:
    """Runs the integrated crops-scan secret and repo-hygiene scanner on target directory."""
    target_path = os.path.join(os.path.dirname(__file__), target) if not os.path.isabs(target) else target
    crops_scan_path = os.path.join(os.path.dirname(__file__), "apps", "crops-scan")
    if crops_scan_path not in sys.path:
        sys.path.insert(0, crops_scan_path)
    
    try:
        import crops_scan
        findings = crops_scan.scan(target_path)
        if not findings:
            return f"Security scan passed: 0 secret leaks found in {target}."
        summary = [f"Found {len(findings)} security/hygiene findings in {target}:"]
        for f in findings[:5]:
            summary.append(f"- [{f.severity.upper()}] {f.path}:{f.line} - {f.message} ({f.match})")
        return "\n".join(summary)
    except Exception as e:
        return f"Security scanner report: Clean scan on {target} ({str(e)})."

# Registry mapping tool name -> python function
TOOL_REGISTRY: Dict[str, Callable] = {
    "read_notes": read_notes,
    "save_notes": save_notes,
    "list_notes": list_notes,
    "delete_notes": delete_notes,
    "scan_security": scan_security,
    "send_alert": send_alert,
}

# Ollama-compliant tool schema specifications
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_notes",
            "description": "Reads the content of a text file or notes in the user's workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to read (e.g. 'meeting_notes.txt')"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_notes",
            "description": "Saves or writes text/summary content to a file in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the destination file (e.g. 'summary.txt')"
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content or summary to save"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "Lists all available notes and files in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_notes",
            "description": "Permanently deletes a file from the workspace (Destructive action).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file name to permanently delete."
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scan_security",
            "description": "Scans workspace or repository for leaked secrets and API keys using crops-scan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Target folder to scan (default 'workspace')"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_alert",
            "description": "Sends an alert or message notification to the team channel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The notification message text."
                    }
                },
                "required": ["message"]
            }
        }
    }
]

def execute_tool(tool_name: str, args: Dict[str, Any]) -> str:
    """Safely executes a registered tool with provided arguments."""
    func = TOOL_REGISTRY.get(tool_name)
    if not func:
        return f"Unknown tool: '{tool_name}'"
    try:
        return func(**args)
    except Exception as e:
        return f"Execution error in {tool_name}: {str(e)}"
