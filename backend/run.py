#!/usr/bin/env python3
"""
ClipGenius Backend Server
Run this script to start the FastAPI server
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting ClipGenius Backend Server...")
    print("📱 Frontend will be available at: http://localhost:3000")
    print("🔧 API will be available at: http://localhost:8000")
    print("📚 API Documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
