import argparse
from loguru import logger
from src.project_files import SearchParams
from src.project_files import ATS_PLATFORMS

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bottom Pot - ATS job scraper")
    parser.add_argument(
        "--strategy",
        default = "serper",
        help = "Search strategy: 'serper' (API recommended) ",
    )

    parser.add_argument(
        "--job-title",
        default="React Native Engineer",
        help="Enter the job title you searched for",
    )

    parser.add_argument(
        "--no-remote", 
        action="store_true", 
        help="Add this filter to remove remote roles"
    )

    parser.add_argument(
        "--days-back",
        type=int,
        default=7, 
        help="Only show the listing from the past N days."
    )

    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Base directory to write results (subdirs json/ and csv/)"
    )

    parser.add_argument(
        "--outputs-prefix",
        default="results",
        help="Prefix for  the output filenames (defaults to 'results'). You can use this to differentiate between different runs or strategies (e.g. 'remote_intern_results' vs 'on_campus_results')",
    )

    parser.add_argument(
        "--location",
        default="United States",
        help="Location to include in the search query (e.g., 'New York', 'London'). This adds location context to job searches and filters results by location mentioned in postings.",
    )

    parser.add_argument(
        "--country-code",
        default=None,
        help="Country code for the search engine's geolocation (e.g., 'us' for google.com, 'gb' for google.co.uk). This restricts search results to a specific country's Google index. Omit for global search.",
    )

    parser.add_argument(
        "--salary-min",
        type=int,
        help="Minimum salary filter (if available)",
    )

    parser.add_argument(
        "--experience-level",
        choices=["entry", "mid", "senior", "lead"],
        help="Filter by experience level",
    )

    parser.add_argument(
        "--exclude-keywords",
        default="",
        help="Comma-separated keywords to exclude from results",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of job listings to retrieve",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )

    return parser.parse_args()

async def main():
    args = parse_args()

    params = SearchParams(
        job_title=args.job_title,
        location=args.location,
        salary_min=args.salary_min,
        experience_level=args.experience_level,
        exclude_keywords=[kw.strip() for kw in args.exclude_keywords.split(",") if kw.strip()],
        max_results=args.max_results,
        remote = not args.no_remote,
        days_back=args.days_back,
        country_code=args.country_code,
    )

    platforms = None

    if args.platforms:
        platforms = [p for p in ATS_PLATFORMS if p.name == args.platforms]
        if not platforms:
            logger.error(f"No valid platforms found for --platforms={args.platforms}. Available options: {[p.name for p in ATS_PLATFORMS]}")
            return

    logger.info(
        f"Bottom Pot - ATS Job Scraper | Strategy: {args.strategy} | Job Title: {params.job_title} | "
        f"Location: {params.location} | Country Code: {params.country_code} | Salary Min: {params.salary_min} | "
        f"Experience Level: {params.experience_level} | Exclude Keywords: {params.exclude_keywords} | "
        f"Max Results: {params.max_results} | Remote: {params.remote} | Days Back: {params.days_back} | "
    )
    
    if args.verbose:
        logger.info(f"Using platforms: {[p.label for p in platforms] if platforms else 'All'}")
        
    # Here you would call your scraping functions, passing in `params` and `platforms` as needed
    if args.strategy == "serper":
        logger.info("Starting scraping using Serper API...")
        # await scrape_with_serper(params, platforms)
        
        

    
    
    if args.verbose:
        logger.info("Scraping completed. Check the output directory for results.")
