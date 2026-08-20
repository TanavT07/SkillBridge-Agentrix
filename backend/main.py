import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skillbridge.api")

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="SkillBridge AI API",
    description="Autonomous Workforce upskilling & Skill-Verification Platform API",
    version="0.1.0",
)

# Configure CORS Middleware
origins = [
    "http://localhost:3000",  # Frontend local dev server (e.g. Next.js / React)
    "http://127.0.0.1:3000",
    "*",  # Allow all for early development / testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOCK_DATA_DIR = Path(__file__).resolve().parent / "mock_data"


@app.get("/")
async def root():
    return {
        "message": "Welcome to SkillBridge AI API",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "skillbridge-backend",
    }


@app.get("/api/mock-jobs")
async def get_mock_jobs():
    """
    Test endpoint to retrieve and combine sample Adzuna and JSearch job datasets
    from the mock_data directory.
    """
    combined_data = {}
    errors = []

    # Read Adzuna mock data
    adzuna_path = MOCK_DATA_DIR / "adzuna_jobs.json"
    try:
        if not adzuna_path.exists():
            raise FileNotFoundError(f"Mock file not found: {adzuna_path.name}")
        with open(adzuna_path, "r", encoding="utf-8") as f:
            combined_data["adzuna"] = json.load(f)
    except Exception as e:
        logger.error(f"Error reading Adzuna mock data: {e}")
        errors.append(f"Adzuna data error: {str(e)}")
        combined_data["adzuna"] = None

    # Read JSearch mock data
    jsearch_path = MOCK_DATA_DIR / "jsearch_jobs.json"
    try:
        if not jsearch_path.exists():
            raise FileNotFoundError(f"Mock file not found: {jsearch_path.name}")
        with open(jsearch_path, "r", encoding="utf-8") as f:
            combined_data["jsearch"] = json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSearch mock data: {e}")
        errors.append(f"JSearch data error: {str(e)}")
        combined_data["jsearch"] = None

    # If both files failed to load, raise HTTP 500
    if combined_data["adzuna"] is None and combined_data["jsearch"] is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to load all mock job datasets.",
                "errors": errors,
            },
        )

    return {
        "status": "success" if not errors else "partial_success",
        "data": combined_data,
        "warnings": errors if errors else None,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
