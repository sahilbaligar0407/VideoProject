from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import video_processing, viral
from app.routers import clips  # Add the new clips router
from app.settings import settings

app = FastAPI(
    title="ClipGenius API",
    description="AI-powered video clip generation with viral optimization",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(video_processing.router, prefix="/api/v1")
app.include_router(viral.router, prefix="/api/v1")
app.include_router(clips.router, prefix="/api/v1")  # Add the new clips router

@app.get("/")
async def root():
    return {
        "message": "ClipGenius API v2.0",
        "description": "AI-powered video clip generation with enhanced Pipeline v2",
        "endpoints": {
            "video_processing": "/api/v1/process-video",
            "viral_engine": "/api/v1/viral",
            "enhanced_clips": "/api/v1/clips/generate",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
