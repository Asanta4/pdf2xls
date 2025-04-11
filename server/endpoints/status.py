import os
import json
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

# Constants from environment variables
TEMP_FOLDER = os.getenv("TEMP_FOLDER", "server/temp_files")

# Create router
router = APIRouter()

# Helper function
def get_session_file_path(session_id: str) -> str:
    """Get the path to the session status file"""
    return os.path.join(TEMP_FOLDER, f"{session_id}.json")

def get_session_status(session_id: str) -> dict:
    """Get session status from a JSON file"""
    status_file = get_session_file_path(session_id)
    if not os.path.exists(status_file):
        raise HTTPException(status_code=404, detail="Session not found")
    
    with open(status_file, "r") as f:
        return json.load(f)

# Endpoints
@router.get("/status/{session_id}")
async def get_status(session_id: str) -> Dict[str, Any]:
    """
    Get the current status of a conversion session
    
    - session_id: UUID of the conversion session
    """
    status = get_session_status(session_id)
    return status

@router.get("/progress/{session_id}")
async def get_progress(session_id: str) -> Dict[str, Any]:
    """
    Get the current progress of a conversion session
    
    - session_id: UUID of the conversion session
    """
    status = get_session_status(session_id)
    
    # Extract relevant fields
    progress_info = {
        "status": status.get("status", "unknown"),
        "progress": status.get("progress", 0),
        "current_page": status.get("current_page", 0),
        "total_pages": status.get("total_pages", 0),
        "error": status.get("error", None)
    }
    
    # Include preview data if conversion is completed
    if status.get("status") == "completed" and "preview" in status:
        progress_info["preview"] = status["preview"]
        progress_info["columns"] = status.get("columns", [])
    
    # Include analysis results if available
    if "analysis" in status:
        progress_info["analysis"] = status["analysis"]
    
    return progress_info

@router.get("/sessions")
async def list_sessions():
    """
    List all active conversion sessions
    """
    try:
        sessions = []
        # List all .json files in the temp folder
        if os.path.exists(TEMP_FOLDER):
            for filename in os.listdir(TEMP_FOLDER):
                if filename.endswith(".json"):
                    session_id = os.path.splitext(filename)[0]
                    try:
                        status = get_session_status(session_id)
                        sessions.append(status)
                    except:
                        # Skip invalid or corrupt status files
                        continue
        
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

@router.get("/preview/{session_id}")
async def get_preview(session_id: str):
    """
    Get a preview of the extracted data (if available)
    
    - session_id: UUID of the conversion session
    """
    status = get_session_status(session_id)
    
    # Check if preview data is available
    if "preview" not in status:
        return {"preview_available": False, "message": "No preview data available"}
    
    return {
        "preview_available": True,
        "data": status["preview"],
        "columns": status.get("columns", [])
    }

@router.post("/reset-preview/{session_id}")
async def reset_preview_data(session_id: str):
    """
    Reset the preview data for a conversion session
    
    - session_id: UUID of the conversion session
    """
    result = reset_preview(session_id)
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to reset preview data"))
    
    return {"success": True, "message": "Preview data has been reset"} 