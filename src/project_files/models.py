from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

# I imported these modules because I need BaseModel for data validation, Optional for type hints,
# and datetime stuff for timestamps. You should know that Pydantic helps me ensure data integrity.

class SearchParams(BaseModel):
    """
    I created this class to hold all the parameters for a job search. You can think of it as a blueprint
    for what the user wants to search for. I use Pydantic so that I can validate the inputs easily.
    For example, job_title is required, but location is optional. I designed it this way because
    not every search needs a location, but every search needs a job title.
    """
    job_title: str  # This is the main thing we're searching for, like "Data Engineer"
    location: Optional[str] = None  # If you want to add a city or region, put it here. not here literally but use that data field.
    salary_min: Optional[int] = None  # Minimum salary in dollars, I add this to the query if provided. cant be working minimum wage lol.
    experience_level: Optional[str] = None  # Like "senior" or "entry", I map this to text
    exclude_keywords: Optional[list[str]] = []  # Words you don't want in results, I exclude them
    max_results: int = 100  # I cap the results at this number to avoid too much data
    remote: Optional[bool] = None  # True for remote only, False to exclude remote, None for both
    days_back: Optional[int] = 7  # How many days back to search, I use this for date filtering
    country_code: Optional[str] = None  # For Google geolocation, like "us" for US results

class ATSConfig(BaseModel):
    """
    I defined this to represent each ATS platform. Each platform has a name, site operator for Google site: search,
    and a human-readable label. I use this to configure which platforms to search.
    """
    name: str  # Short name like "greenhouse"
    site_operator: str  # The domain part, like "greenhouse.io"
    label: str  # Friendly name, like "Greenhouse"

class RawSearchResults(BaseModel):
    """
    This is what I store for each search result. I included the URL, title, snippet, which ATS it came from,
    the query that found it, and when I scraped it. I use this to track everything.
    """
    url: str  # The job posting URL
    title: str  # The job title from the search result
    snippet: Optional[str]  # A preview text from Google
    ats_source: str  # Which platform, like "greenhouse"
    query_used: str  # The exact Google query I used
    scraped_at: datetime = datetime.now(timezone.utc)  # Timestamp when I got this result 
