"""
Main FastAPI Application
Parul University Admission AI Assistant
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api import auth, voice
from app.data.data_loader import get_data_loader
from app.utils.logger import logger

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""

    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("Loading knowledge base...")

    # Initialize data loader (loads all JSON data)
    data_loader = get_data_loader()
    logger.info(f"Loaded {len(data_loader.courses)} courses")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered admission assistant for Parul University",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(voice.router)


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "auth": "/api/auth",
            "voice": "/api/voice"
        }
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# Get available courses
@app.get("/api/courses")
async def get_courses():
    """Get all available courses"""
    data_loader = get_data_loader()
    return {
        "courses": data_loader.courses,
        "count": len(data_loader.courses)
    }


# Get course by ID
@app.get("/api/courses/{course_id}")
async def get_course(course_id: str):
    """Get specific course details"""
    data_loader = get_data_loader()
    course = data_loader.get_course_by_id(course_id)

    if not course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Course not found")

    return course


# Get fees for course
@app.get("/api/fees/{course_id}")
async def get_fees(course_id: str):
    """Get fee structure for a course"""
    data_loader = get_data_loader()
    fees = data_loader.get_fees_by_course_id(course_id)

    if not fees:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Fee structure not found")

    return fees


# Calculate scholarship
@app.get("/api/scholarship/calculate")
async def calculate_scholarship(course_id: str, percentage: float):
    """Calculate scholarship based on percentage"""
    data_loader = get_data_loader()
    scholarship = data_loader.calculate_scholarship(percentage, course_id)

    return scholarship


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS
    )
