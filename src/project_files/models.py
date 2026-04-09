from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

class SearchParams(BaseModel):
    job_title: str
    location: Optional[str] = None  # Location to include in search query (e.g., "New York")
    salary_min: Optional[int] = None
    experience_level: Optional[str] = None
    exclude_keywords: Optional[list[str]] = []
    max_results: int = 100
    remote: Optional[bool] = None
    days_back: Optional[int] = 7  # Number of days back to filter job postings (default to 7 days)
    country_code: Optional[str] = None  # Country code for search engine geolocation (e.g., "us" for google.com)


class ATSConfig(BaseModel):
    name: str
    site_operator: str
    label: str

class RawSearchResults(BaseModel):
    url: str
    title: str
    snippet : Optional[str]
    ats_source: str  # which ATS platform this came from
    query_used: str  # log exactly what query produced this result
    scraped_at: datetime = datetime.now(timezone.utc)
