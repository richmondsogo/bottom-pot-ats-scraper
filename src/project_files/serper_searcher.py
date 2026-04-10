import httpx
from typing import Optional
from loguru import logger

from src.project_files.config import (
    ATS_PLATFORMS,
    SERPER_API_KEY,
    SERPER_ENDPOINT,
    SERPER_MAX_PAGES,
)
from src.project_files.models import ATSConfig, RawSearchResults, SearchParams
from src.project_files.query_builder import QueryBuilder


class SerperSearcher:
    """
    Queries Google Search via Serper.dev's JSON API.

    Each paginated request costs 1 Serper credit.
    Budget per full run across all platforms at 3 pages each: ~60 credits.
    With 2,500 free credits that's ~41 full runs before you need to pay.

    Usage:
        searcher = SerperSearcher()
        results = await searcher.run(SearchParams(job_title="Data Engineer"))
    """

    def __init__(self):
        if not SERPER_API_KEY:
            raise RuntimeError(
                "Serper API key not found. Please set SERPER_API_KEY in your .env file."
            )
        self.headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        }

    async def _search_page(
        self,
        client: httpx.AsyncClient,
        query: str,
        page: int,
        country_code: Optional[str],
        days_back: Optional[int],
    ) -> dict:
        """
        Makes a single paginated Serper API request (1 credit per call).

        `page` is 1-indexed. We fix `num` at 10 so credit cost stays predictable;
        raise it (up to 100) if you want more results per credit at the cost of
        less granular pagination logging.
        """
        payload: dict = {
            "q": query,
            "page": page,
            "num": 10,
            "hl": "en",
            "tbs": f"qdr:d{days_back}" if days_back and days_back > 0 else "qdr:d7",
        }

        if country_code:
            payload["gl"] = country_code

        try:
            response = await client.post(
                SERPER_ENDPOINT,
                json=payload,
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise RuntimeError("Serper API key is invalid or quota is exhausted.")
            logger.error(
                f"Serper HTTP {e.response.status_code} on page {page} for query: {query}"
            )
            return {}

    def _parse_response(
        self,
        data: dict,
        ats: ATSConfig,
        query_str: str,
    ) -> list[RawSearchResults]:
        """
        Extracts and validates organic results from a Serper response.

        Serper returns results under data["organic"], each with:
            - link     (the URL)
            - title
            - snippet
            - date     (relative, e.g. "3 hours ago") — useful for dedup later
        """
        results: list[RawSearchResults] = []

        for item in data.get("organic", []):
            url = item.get("link", "")
            title = item.get("title", "")

            if not url.startswith("https") or not title:
                continue

            # Belt-and-braces: confirm the result belongs to the ATS we queried.
            if ats.site_operator not in url:
                logger.debug(f"Skipping off-domain result: {url}")
                continue

            results.append(
                RawSearchResults(
                    url=url,
                    title=title,
                    snippet=item.get("snippet", "").strip() or None,
                    ats_source=ats.name,
                    query_used=query_str,
                )
            )

        return results

    async def search_ats_platform(
        self,
        client: httpx.AsyncClient,
        ats: ATSConfig,
        params: SearchParams,
        query_str: str,
    ) -> list[RawSearchResults]:
        """
        Searches one ATS platform across all configured pages.

        Always runs the full SERPER_MAX_PAGES — Google may surface different
        listings on later pages regardless of how many came back on earlier ones,
        so we never stop early.
        """
        all_results: list[RawSearchResults] = []

        for page in range(1, SERPER_MAX_PAGES + 1):
            logger.debug(f"[{ats.label}] Fetching page {page} | query: {query_str}")

            data = await self._search_page(
                client,
                query_str,
                page,
                country_code=params.country_code,
                days_back=params.days_back,
            )

            page_results = self._parse_response(data, ats, query_str)
            all_results.extend(page_results)
            logger.info(
                f"[{ats.label}] Page {page}/{SERPER_MAX_PAGES} → {len(page_results)} results"
            )

        return all_results

    async def run(
        self,
        params: SearchParams,
        platforms: Optional[list[ATSConfig]] = None,
    ) -> list[RawSearchResults]:
        """
        Runs the full search across all (or selected) ATS platforms.

        Results are capped at params.max_results after all platforms are searched
        so the caller gets a predictable upper bound.
        """
        all_results: list[RawSearchResults] = []
        target_platforms = platforms or ATS_PLATFORMS

        async with httpx.AsyncClient(timeout=30.0) as client:
            for ats in target_platforms:
                query_str = QueryBuilder(ats).build_query_string(params)
                logger.info(f"[{ats.label}] Starting search | query: {query_str}")

                platform_results = await self.search_ats_platform(
                    client, ats, params, query_str
                )
                all_results.extend(platform_results)

                logger.success(
                    f"[{ats.label}] Done — {len(platform_results)} results "
                    f"(running total: {len(all_results)})"
                )

        if params.max_results:
            all_results = all_results[: params.max_results]
            logger.info(f"Results capped at max_results={params.max_results}")

        return all_results
