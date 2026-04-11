from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from src.project_files.models import ATSConfig, SearchParams

# I defined the base Google search URL here because I use it for debug purposes.
# You can paste this URL into your browser to see what the search looks like.
GOOGLE_BASE_URL = "https://www.google.com/search"


class QueryBuilder:
    """
    I built this class to construct Google search queries tailored for ATS platforms.
    It's not for Playwright; it's for generating query strings that I send to Serper API.
    I take the search params and the ATS config to build a precise query.
    """

    # I mapped experience levels to more natural text because Google understands "entry level" better than "entry".
    # You can see I have mappings for entry, mid, senior, lead.
    EXPERIENCE_MAPPING = {
        "entry": "entry level",
        "mid": "mid level",
        "senior": "senior",
        "lead": "lead",
    }

    def __init__(self, ats: ATSConfig):
        # I stored the ATS config so I know which platform I'm building queries for.
        # You pass an ATSConfig instance when creating this builder.
        self.ats = ats

    def build_query_string(self, params: SearchParams) -> str:
        """
        I constructed the main query string from the search params.
        I start with site: operator, then add job title, location, etc.
        I return a string that looks like a Google query.
        """
        # I always include the site operator to limit to this ATS platform.
        parts: list[str] = [f"site:{self.ats.site_operator}"]

        # I cleaned the job title and quote it if it has spaces.
        title = params.job_title.strip()
        parts.append(f'"{title}"' if " " in title else title)

        # If location is provided, I add it, quoting if needed.
        if params.location:
            location = params.location.strip()
            if location:
                parts.append(f'"{location}"' if " " in location else location)

        # For remote, I add "remote" or exclude it with -.
        if params.remote is True:
            parts.append('"remote"')
        elif params.remote is False:
            parts.append('-"remote"')

        # I add salary if specified.
        if params.salary_min is not None:
            parts.append(f"${params.salary_min}")

        # I map experience level and add it.
        if params.experience_level:
            experience_text = self.EXPERIENCE_MAPPING.get(
                params.experience_level,
                params.experience_level,
            )
            parts.append(f'"{experience_text}"')

        # I calculate the cutoff date and add after: filter.
        if params.days_back is not None and params.days_back > 0:
            cutoff_date = (
                datetime.now(timezone.utc) - timedelta(days=params.days_back)
            ).date()
            parts.append(f"after:{cutoff_date.isoformat()}")

        # I excludedd keywords by prefixing with -.
        for keyword in params.exclude_keywords or []:
            cleaned = keyword.strip()
            if not cleaned:
                continue
            if " " in cleaned:
                parts.append(f'-"{cleaned}"')
            else:
                parts.append(f"-{cleaned}")

        # I join all parts with spaces to form the query.
        return " ".join(parts)

    def build_serper_payload(
        self,
        params: SearchParams,
        page: int = 1,
        num: int = 10,
    ) -> dict:
        """
        I build the payload for Serper API. It's a dict with query, page, num, etc.
        I use this to send to Serper.
        """
        payload = {
            "q": self.build_query_string(params),
            "page": page,
            "num": num,
            "hl": "en",
        }

        # If country code is present, add gl for geolocation.
        if params.country_code:
            payload["gl"] = self.normalize_country_code(params.country_code)

        return payload

    @staticmethod
    def normalize_country_code(country_code: Optional[str]) -> Optional[str]:
        """
        I normalize the country code to lowercase and stripped.
        You can pass "US" or "us", I make it "us".
        """
        if not country_code:
            return None
        return country_code.strip().lower()

    def build_debug_url(self, params: SearchParams, page: int = 0) -> str:
        """
        I create a debug URL that you can open in browser to see the search results.
        It's useful for testing queries.
        """
        query_string = self.build_query_string(params)
        url_params = {
            "q": query_string,
            "start": page * 10,
            "num": 10,
        }
        if params.country_code:
            url_params["gl"] = self.normalize_country_code(params.country_code)
        return f"{GOOGLE_BASE_URL}?{urlencode(url_params)}"
