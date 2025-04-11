import os
import uuid
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Constants from environment variables
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10485760))  # 10MB default
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
TEMP_FOLDER = os.getenv("TEMP_FOLDER", "server/temp_files")

# Create router
router = APIRouter()

# Define conversion status states
class ConversionStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

# Helper functions
def get_session_file_path(session_id: str) -> str:
    """Get the path to the session status file"""
    return os.path.join(TEMP_FOLDER, f"{session_id}.json")

def save_session_status(session_id: str, status: dict) -> None:
    """Save session status to a JSON file"""
    with open(get_session_file_path(session_id), "w") as f:
        json.dump(status, f)

def get_session_status(session_id: str) -> dict:
    """Get session status from a JSON file"""
    status_file = get_session_file_path(session_id)
    if not os.path.exists(status_file):
        raise HTTPException(status_code=404, detail="Session not found")
    
    with open(status_file, "r") as f:
        return json.load(f)

def validate_file(file: UploadFile) -> None:
    """Validate file type and size"""
    # Check file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Get file size (FastAPI stores uploaded file in memory by default)
    # We'll use a small read to check content type
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset file position
    
    # Check file size
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({MAX_UPLOAD_SIZE/1024/1024:.1f}MB)"
        )

# Endpoints
@router.post("/upload", status_code=HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF file and create a new conversion session
    
    Returns a session UUID to track the conversion process
    """
    # Validate the file
    validate_file(file)
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Create directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(UPLOAD_FOLDER, f"{session_id}.pdf")
    with open(file_path, "wb") as f:
        contents = await file.read()
        f.write(contents)
    
    # Initialize session status
    status = {
        "session_id": session_id,
        "filename": file.filename,
        "status": ConversionStatus.PENDING,
        "progress": 0,
        "current_page": 0,
        "total_pages": 0,
        "output_format": None,
        "output_path": None,
        "created_at": str(Path(file_path).stat().st_ctime)
    }
    
    # Save the session status
    save_session_status(session_id, status)
    
    return {"session_id": session_id, "status": status["status"]}

@router.post("/start/{session_id}")
async def start_conversion(
    session_id: str, 
    background_tasks: BackgroundTasks,
    output_format: str = Form(...),
):
    """
    Start the conversion process for a previously uploaded PDF
    
    - session_id: UUID of the conversion session
    - output_format: Output format ('csv' or 'xlsx')
    """
    # Validate output format
    if output_format not in ["csv", "xlsx"]:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Invalid output format. Use 'csv' or 'xlsx'"
        )
    
    # Get current session status
    status = get_session_status(session_id)
    
    # Check if file exists
    file_path = os.path.join(UPLOAD_FOLDER, f"{session_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Update session status
    status["status"] = ConversionStatus.PROCESSING
    status["output_format"] = output_format
    save_session_status(session_id, status)
    
    # Start conversion in background
    from server.utils.converter import start_conversion_task
    background_tasks.add_task(start_conversion_task, session_id, output_format)
    
    return {"session_id": session_id, "status": status["status"]}

@router.post("/pause/{session_id}")
async def pause_conversion(session_id: str):
    """
    Pause an ongoing conversion process
    
    - session_id: UUID of the conversion session
    """
    # Get current session status
    status = get_session_status(session_id)
    
    # Check if process can be paused
    if status["status"] != ConversionStatus.PROCESSING:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause conversion in {status['status']} status"
        )
    
    # Update session status
    status["status"] = ConversionStatus.PAUSED
    save_session_status(session_id, status)
    
    return {"session_id": session_id, "status": status["status"]}

@router.post("/resume/{session_id}")
async def resume_conversion(session_id: str, background_tasks: BackgroundTasks):
    """
    Resume a paused conversion process
    
    - session_id: UUID of the conversion session
    """
    # Get current session status
    status = get_session_status(session_id)
    
    # Check if process can be resumed
    if status["status"] != ConversionStatus.PAUSED:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume conversion in {status['status']} status"
        )
    
    # Update session status
    status["status"] = ConversionStatus.PROCESSING
    save_session_status(session_id, status)
    
    # Resume conversion in background
    from server.utils.converter import resume_conversion_task
    background_tasks.add_task(
        resume_conversion_task, 
        session_id, 
        status["output_format"]
    )
    
    return {"session_id": session_id, "status": status["status"]}

@router.post("/cancel/{session_id}")
async def cancel_conversion(session_id: str):
    """
    Cancel a conversion process and reset progress
    
    - session_id: UUID of the conversion session
    """
    # Get current session status
    status = get_session_status(session_id)
    
    # Update session status
    status["status"] = ConversionStatus.PENDING
    status["progress"] = 0
    status["current_page"] = 0
    save_session_status(session_id, status)
    
    # Remove any temporary output files
    if status.get("output_path") and os.path.exists(status["output_path"]):
        os.remove(status["output_path"])
        status["output_path"] = None
        save_session_status(session_id, status)
    
    return {"session_id": session_id, "status": status["status"]}

@router.get("/download/{session_id}")
async def download_file(session_id: str):
    """
    Download the converted file
    
    - session_id: UUID of the conversion session
    """
    # Get current session status
    status = get_session_status(session_id)
    
    # Check if conversion is completed
    if status["status"] != ConversionStatus.COMPLETED:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Conversion is not completed (current status: {status['status']})"
        )
    
    # Check if output file exists
    if not status.get("output_path") or not os.path.exists(status["output_path"]):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    # Get original filename without extension
    original_filename = os.path.splitext(status["filename"])[0]
    
    # Create response with the file
    extension = status["output_format"]
    filename = f"{original_filename}.{extension}"
    
    return FileResponse(
        path=status["output_path"],
        filename=filename,
        media_type="application/octet-stream"
    ) 