import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("skillbridge.job_apis")

# Path to mock data directory
MOCK_DATA_DIR = Path(__file__).resolve().parent.parent / "mock_data"


def _load_mock_data(filename: str) -> Dict[str, Any]:
    """Load JSON fallback data from the mock_data directory."""
    file_path = MOCK_DATA_DIR / filename
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        logger.warning(f"Mock data file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error reading mock data file {filename}: {e}")
    return {}


async def fetch_adzuna_jobs(
    query: str = "software engineer",
    location: str = "us",
    page: int = 1,
    results_per_page: int = 10,
    country: str = "us",
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    Fetch job listings asynchronously from Adzuna API.
    Falls back to mock data if API keys are missing or the request fails.

    Env variables expected:
        - ADZUNA_APP_ID
        - ADZUNA_APP_KEY
    """
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        logger.info("Adzuna API credentials missing. Returning mock data.")
        mock = _load_mock_data("adzuna_jobs.json")
        mock["source"] = "mock_fallback"
        return mock

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": results_per_page,
        "what": query,
        "where": location,
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            data["source"] = "adzuna_live"
            return data
    except Exception as e:
        logger.error(f"Failed to fetch jobs from Adzuna: {e}. Falling back to mock data.")
        mock = _load_mock_data("adzuna_jobs.json")
        mock["source"] = "mock_fallback"
        mock["error"] = str(e)
        return mock


async def fetch_jsearch_jobs(
    query: str = "Python Developer",
    page: int = 1,
    num_pages: int = 1,
    country: str = "us",
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    Fetch job listings asynchronously from JSearch API (via RapidAPI).
    Falls back to mock data if API keys are missing or the request fails.

    Env variables expected:
        - RAPIDAPI_KEY or JSEARCH_API_KEY
        - RAPIDAPI_HOST (default: jsearch.p.rapidapi.com)
    """
    api_key = os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY") or os.getenv("JSEARCH_API_KEY")
    api_host = os.getenv("RAPIDAPI_HOST", "jsearch.p.rapidapi.com")

    if not api_key:
        logger.info("JSearch / RapidAPI key missing. Returning mock data.")
        mock = _load_mock_data("jsearch_jobs.json")
        mock["source"] = "mock_fallback"
        return mock

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
    }
    params = {
        "query": f"{query} in {country}",
        "page": str(page),
        "num_pages": str(num_pages),
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            data["source"] = "jsearch_live"
            return data
    except Exception as e:
        logger.error(f"Failed to fetch jobs from JSearch: {e}. Falling back to mock data.")
        mock = _load_mock_data("jsearch_jobs.json")
        mock["source"] = "mock_fallback"
        mock["error"] = str(e)
        return mock


async def fetch_aggregated_jobs(
    query: str = "Python Developer",
    location: str = "remote",
) -> Dict[str, Any]:
    """
    Query both Adzuna and JSearch concurrently and return an aggregated payload.
    """
    import asyncio

    adzuna_task = fetch_adzuna_jobs(query=query, location=location)
    jsearch_task = fetch_jsearch_jobs(query=query)

    adzuna_res, jsearch_res = await asyncio.gather(
        adzuna_task, jsearch_task, return_exceptions=True
    )

    adzuna_data = adzuna_res if isinstance(adzuna_res, dict) else {"error": str(adzuna_res)}
    jsearch_data = jsearch_res if isinstance(jsearch_res, dict) else {"error": str(jsearch_res)}

    return {
        "query": query,
        "location": location,
        "adzuna": adzuna_data,
        "jsearch": jsearch_data,
    }
