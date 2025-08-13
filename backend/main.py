from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import video_processing
from app.config import settings

app = FastAPI(
    title="ClipGenius API",
    description="AI-powered video highlight generation with transcription and captioning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(video_processing.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "ClipGenius API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
