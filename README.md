# Bottom Pot ATS Scraper

## About
Bottom Pot is an automated ATS job scraper that bypasses traditional job aggregators and pulls fresh listings directly from ATS platforms.

## Description
Bottom Pot is a Python based job scraping pipeline built to search ATS platforms such as Ashby, Greenhouse, Lever, Workable, and BambooHR directly instead of relying on LinkedIn or Indeed.

It uses parameterized Google search queries with job title keywords, remote filters, and date thresholds to discover only relevant and recent openings. The search is performed via the Serper.dev API, which provides access to Google Search results programmatically.

Scraped listings are normalized, deduplicated across platforms, and stored in JSON and CSV formats for easy analysis.

## Tech Stack
Python, httpx, Serper API, pandas
 