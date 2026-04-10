from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

from src.project_files.models import ATSConfig, SearchParams

GOOGLE_BASE_URL = "https://www.google.com/search"


class QueryBuilder:
    """
    Builds Serper-compatible Google search query strings for ATS platforms.

    This is not a Playwright URL builder; it generates the raw query text and
    a minimal Serper request payload for use with the Serper JSON API.
    """

    EXPERIENCE_MAPPING = {
        "entry": "entry level",
        "mid": "mid level",
        "senior": "senior",
        "lead": "lead",
    }

    def __init__(self, ats: ATSConfig):
        self.ats = ats

    def build_query_string(self, params: SearchParams) -> str:
        parts: list[str] = [f"site:{self.ats.site_operator}"]

        title = params.job_title.strip()
        parts.append(f'"{title}"' if " " in title else title)

        if params.location:
            location = params.location.strip()
            if location:
                parts.append(f'"{location}"' if " " in location else location)

        if params.remote is True:
            parts.append('"remote"')
        elif params.remote is False:
            parts.append('-"remote"')

        if params.salary_min is not None:
            parts.append(f"${params.salary_min}")

        if params.experience_level:
            experience_text = self.EXPERIENCE_MAPPING.get(
                params.experience_level,
                params.experience_level,
            )
            parts.append(f'"{experience_text}"')

        if params.days_back is not None and params.days_back > 0:
            cutoff_date = (
                datetime.now(timezone.utc) - timedelta(days=params.days_back)
            ).date()
            parts.append(f"after:{cutoff_date.isoformat()}")

        for keyword in params.exclude_keywords or []:
            cleaned = keyword.strip()
            if not cleaned:
                continue
            if " " in cleaned:
                parts.append(f'-"{cleaned}"')
            else:
                parts.append(f"-{cleaned}")

        return " ".join(parts)

    def build_serper_payload(
        self,
        params: SearchParams,
        page: int = 1,
        num: int = 10,
    ) -> dict:
        payload = {
            "q": self.build_query_string(params),
            "page": page,
            "num": num,
            "hl": "en",
        }

        if params.country_code:
            payload["gl"] = self.normalize_country_code(params.country_code)

        return payload

    @staticmethod
    def normalize_country_code(country_code: Optional[str]) -> Optional[str]:
        if not country_code:
            return None
        return country_code.strip().lower()

    def build_debug_url(self, params: SearchParams, page: int = 0) -> str:
        query_string = self.build_query_string(params)
        url_params = {
            "q": query_string,
            "start": page * 10,
            "num": 10,
        }
        if params.country_code:
            url_params["gl"] = self.normalize_country_code(params.country_code)
        return f"{GOOGLE_BASE_URL}?{urlencode(url_params)}"
