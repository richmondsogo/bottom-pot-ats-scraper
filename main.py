import asyncio
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from src.project_files import ATS_PLATFORMS, SearchParams


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bottom Pot — scrape ATS platforms for job listings via Google Search.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Search strategy
    parser.add_argument(
        "--strategy",
        default="serper",
        choices=["serper"],
        help="Search backend to use.",
    )

    # Core search params
    parser.add_argument(
        "--job-title",
        required=True,
        help="Job title to search for (e.g. 'React Native Engineer').",
    )
    parser.add_argument(
        "--location",
        default=None,
        help="Location context added to the query (e.g. 'New York', 'London').",
    )
    parser.add_argument(
        "--country-code",
        default=None,
        help=(
            "Restrict results to a country's Google index "
            "(e.g. 'us' for google.com, 'gb' for google.co.uk). "
            "Omit for a global search."
        ),
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="Only return listings posted within the last N days.",
    )
    remote_group = parser.add_mutually_exclusive_group()
    remote_group.add_argument(
        "--remote",
        action="store_true",
        default=False,
        help="Only return remote roles (adds '\"remote\"' to the query).",
    )
    remote_group.add_argument(
        "--no-remote",
        action="store_true",
        default=False,
        help="Exclude remote roles (adds '-\"remote\"' to the query).",
    )

    # Filters
    parser.add_argument(
        "--salary-min",
        type=int,
        default=None,
        help="Minimum salary hint included in the query (e.g. 80000).",
    )
    parser.add_argument(
        "--experience-level",
        choices=["entry", "mid", "senior", "lead"],
        default=None,
        help="Filter by experience level.",
    )
    parser.add_argument(
        "--exclude-keywords",
        default="",
        help="Comma-separated keywords to exclude (e.g. 'intern,contract,part-time').",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Cap on total results returned across all platforms.",
    )

    # Platform selection
    parser.add_argument(
        "--platforms",
        default=None,
        help=(
            "Comma-separated ATS platform names to search "
            "(e.g. 'greenhouse,lever'). Omit to search all platforms. "
            f"Available: {', '.join(p.name for p in ATS_PLATFORMS)}"
        ),
    )

    # Output
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Base directory for results (json/ and csv/ sub-dirs are created automatically).",
    )
    parser.add_argument(
        "--output-prefix",
        default="results",
        help="Filename prefix for output files (e.g. 'remote_senior_results').",
    )

    # Logging
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    args = parse_args()

    # Configure log level before anything else logs.
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if args.verbose else "INFO",
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )

    # Build SearchParams from CLI args.
    params = SearchParams(
        job_title=args.job_title,
        location=args.location,
        country_code=args.country_code,
        days_back=args.days_back,
        remote=True if args.remote else (False if args.no_remote else None),
        salary_min=args.salary_min,
        experience_level=args.experience_level,
        exclude_keywords=[
            kw.strip() for kw in args.exclude_keywords.split(",") if kw.strip()
        ],
        max_results=args.max_results,
    )

    # Resolve platforms.
    platforms = None
    if args.platforms:
        requested = {name.strip().lower() for name in args.platforms.split(",")}
        platforms = [p for p in ATS_PLATFORMS if p.name in requested]
        if not platforms:
            logger.error(
                f"No matching platforms for: {args.platforms}. "
                f"Available names: {[p.name for p in ATS_PLATFORMS]}"
            )
            return

    logger.info(
        f"Bottom Pot | strategy={args.strategy} | job_title={params.job_title!r} | "
        f"location={params.location!r} | country_code={params.country_code} | "
        f"days_back={params.days_back} | remote={params.remote} | "
        f"salary_min={params.salary_min} | experience_level={params.experience_level} | "
        f"exclude_keywords={params.exclude_keywords} | max_results={params.max_results} | "
        f"platforms={[p.name for p in platforms] if platforms else 'all'}"
    )

    # Run search.
    results = []
    if args.strategy == "serper":
        from src.project_files.serper_searcher import SerperSearcher

        results = await SerperSearcher().run(params, platforms)

    # Print a summary to stdout.
    print(f"\n{'─' * 60}")
    print(f"  Found {len(results)} result(s)")
    print(f"{'─' * 60}\n")
    for r in results:
        print(f"[{r.ats_source.upper()}] {r.title}")
        if r.snippet:
            print(f"  {r.snippet}")
        print(f"  {r.url}")
        print(f"  Query: {r.query_used}\n")

    # Save outputs.
    output_dir = Path(args.output_dir)
    json_dir = output_dir / "json"
    csv_dir = output_dir / "csv"
    json_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_path = json_dir / f"{args.output_prefix}_results.json"
    csv_path = csv_dir / f"{args.output_prefix}_results.csv"

    json_path.write_text(
        json.dumps(
            [r.model_dump(mode="json") for r in results], ensure_ascii=False, indent=4
        ),
        encoding="utf-8",
    )

    if results:
        pd.DataFrame([r.model_dump(mode="json") for r in results]).to_csv(
            csv_path, index=False, encoding="utf-8-sig"
        )

    print(f"{'─' * 60}")
    print(f"  Saved {len(results)} result(s) at {timestamp}")
    print(f"  JSON → {json_path}")
    print(f"  CSV  → {csv_path}")
    print(f"{'─' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
