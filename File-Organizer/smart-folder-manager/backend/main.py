"""
Smart Folder Manager Backend
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from app.api.routes import scan, classify, duplicates, actions, undo, history, file_movements, collisions, db_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app/logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Smart Folder Manager API",
    description="ML-powered file organization system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# Include routers
app.include_router(scan.router, prefix="/api/scan-folder", tags=["Folder Operations"])
app.include_router(classify.router, prefix="/api/classify-files", tags=["Classification"])
app.include_router(duplicates.router, prefix="/api/detect-duplicates", tags=["Duplicates"])
app.include_router(collisions.router, prefix="/api/collisions", tags=["Collision Detection"])
app.include_router(actions.router, prefix="/api/apply-action", tags=["Actions"])
app.include_router(undo.router, prefix="/api/undo", tags=["Undo"])
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(file_movements.router, prefix="/api", tags=["File Movements History"])
app.include_router(db_sync.router, prefix="/api/db-sync", tags=["Database Synchronization"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Folder Manager API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart Folder Manager Backend"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Smart Folder Manager Backend")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
