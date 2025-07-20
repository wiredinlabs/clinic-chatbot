from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, clinics, users, health
from app.config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="Multi-Clinic Chatbot API",
    description="AI-powered chatbot system supporting multiple clinics and users",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat.router, prefix="/api/v1")
app.include_router(clinics.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

# Legacy endpoint for backward compatibility
app.include_router(chat.router, tags=["legacy"])

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Multi-Clinic Chatbot API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )