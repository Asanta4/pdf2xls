import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Create necessary directories if they don't exist
Path(os.getenv("UPLOAD_FOLDER", "uploads")).mkdir(exist_ok=True)
Path(os.getenv("TEMP_FOLDER", "server/temp_files")).mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="PDF to Excel/CSV Converter API",
    description="API for converting PDF files to Excel or CSV format",
    version="1.0.0",
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
origins.append("http://localhost:8003")  # Add our API server to allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use the origins from environment variables
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
# These will be created in separate files later
from server.endpoints import conversion, status

# Register routers
app.include_router(conversion.router, prefix="", tags=["Conversion"])
app.include_router(status.router, prefix="", tags=["Status"])

@app.get("/")
async def root():
    """Root endpoint to verify API is running"""
    return {"message": "PDF to Excel/CSV Converter API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Test endpoint
@app.get("/test")
async def test():
    """Test endpoint to verify API is accessible"""
    return {"message": "Test endpoint is working"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run("server.main:app", host=host, port=port, reload=debug) 