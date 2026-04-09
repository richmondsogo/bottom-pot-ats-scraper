import httpx
from typing import Optional
from loguru import logger
from src.project_files.config import SERPER_ENDPOINT, SERPER_API_KEY, SERPER_MAX_PAGES
from src.project_files.models import ATSConfig, RawSearchResults, SearchParams
from src.project_files.query_builder import QueryBuilder


class SerperSearcher:
    """
    Queries Google Search via Serper.dev's JSON API.

    Each paginated request costs 1 Serper credit.

    Budget per full run (all platforms, 3 pages each):
        7 platforms × 3 pages = 21 credits

    With 2,500 free credits that's ~119 full runs before you need to pay.

    Usage:
        searcher = SerperSearcher()
        results = await searcher.run(SearchParams(job_title="Data Engineer"))
    """
    def __init__(self):
        if not SERPER_API_KEY:
            raise RuntimeError(f"Serper API key not found. Please set the {SERPER_API_KEY} environment variable.in a .env file in the main")

        self.headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }

    async def _search_page(
        self, 
        client: httpx.AsyncClient,
        query: str, 
        page: int,
        country_code: Optional[str] = "us",
        days_back: Optional[int] = None,
    ) -> dict:
        """
        Makes a single Serper API request.

        Serper paginates with `page` (1-indexed) and returns up to 10 results.
        The `num` field can go up to 100 but costs proportionally more credits.
        We keep it at 10 per page and paginate manually for transparency.
        """
        if days_back is not None and days_back > 0:
            tbs_value = f"qdr:d{days_back}"
        else:
            tbs_value = f"qdr:d{7}"

        payload = {
            "q": query,
            "page": page,  # 1-indexed page number for pagination
            "num": 10,  # results per page (max 100, costs more credits)
            "hl": "en",  # language of the search results (English)
            "tbs": tbs_value,
        }

        if country_code:
            payload["gl"] = country_code  # geolocation (country code, e.g., "us", "gb"); omit for global search

        try:
            response = await client.post(
                SERPER_ENDPOINT,
                json=payload, 
                headers=self.headers,
                timeout=30.0,  # seconds
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise RuntimeError("Serper API key invalid or quota exhausted.")
            logger.error(f"Serper HTTP error: {e.response.status_code}")
            return {}

    def _parse_response(
        self,
        data: dict,
        ats: ATSConfig,
        query_str: str,
    ) -> list[RawSearchResults]:
        """
        Parses Serper API response and extracts relevant fields.

        We also log the original query used to generate each result for traceability.
        
        Serper returns organic results under data["organic"], each with:
            - link  (the URL)
            - title
            - snippet
            - date  (relative, e.g. "19 hours ago") — useful for dedup later
        """
        results: list[RawSearchResults] = []

        for item in data.get("organic", []):
            url = item.get("link")
            if not url or not url.startswith("https"):
                continue

            # Confirm the result is actually from the ATS we queried
            # Serper is reliable here, but belt-and-braces doesn't hurt
            if ats.site_operator not in url:
                logger.debug(f"Filtered out off-domain result: {url}")
                continue

            title = item.get("title")
            snippet = item.get("snippet", "").strip() or None

            if url and title:
                results.append(RawSearchResults(
                    url=url,
                    title=title,
                    snippet=snippet,
                    ats_source=ats.name,
                    query_used=query_str,
                ))
        return results

    async def search_ats_platform(
        self,
        client: httpx.AsyncClient,
        ats: ATSConfig,
        params: SearchParams,
        query_str: str,
        country_code: Optional[str] = "us",
        days_back: Optional[int] = None,
    ) -> list[RawSearchResults]:
        """
        Searches a single ATS platform across multiple pages and aggregates results.

        We paginate up to SERPER_MAX_PAGES to get more results, but this can be adjusted.
        """
        builder = QueryBuilder(ats)
        payload = builder.build_serper_payload(params, page=page)
        data = await client.post(SERPER_ENDPOINT, json=payload, headers=self.headers)
                        
        all_results: list[RawSearchResults] = []

        for page in range(1, SERPER_MAX_PAGES + 1):
            logger.debug(f"Searching {ats.label} (page {page}) with query: {query_str}")
            logger.debug(f"Serper search payload: {{'q': {query_str}, 'page': {page}, 'num': 10, 'hl': 'en', 'tbs': 'qdr:d{days_back}', 'gl': {country_code}}}")
            
            logger.info(f"Searching {ats.label} (page {page}) with query: {query_str}")


            
            data = await self._search_page(client, query_str, page, country_code, days_back)
            page_results = self._parse_response(data, ats, query_str)
            all_results.extend(page_results)

            # If we get fewer than 10 results, it's likely the last page
            if len(page_results) < 10:
                break

        return all_results

    # await self._search_page(
    #     client, query, page, country_code=params.country_code, days_back=params.days_back
    # )
