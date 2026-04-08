import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bottom Pot - ATS job scraper")
    parser.add_argument(
        "--strategy",
        choices = ["serper", "playwright"],
        default = "serper",
        help = "Search strategy: 'serper' (API recommended) or playwright (browser fallback)",
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
        help="Prefix for outputs filenames (defaults to 'results'). ",
    )

    parser.add_argument(
        "--location",
        default="United States",
        help="Job location or region to filter by",
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
