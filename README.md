# GitHub Repository Stars Crawler
## Project Overview

This project is a GitHub repository crawler using GitHub’s GraphQL API.
It fetches repositories incrementally based on their star counts and stores their metadata in a PostgreSQL database.
The project is designed for scalability and continuous daily crawling, respecting GitHub rate limits.

Key features:

* Incremental crawling of repositories by star ranges.
* Efficient storage in a relational database.
* Modular design following clean architecture principles.
* Handles API errors and retries automatically. 

## Project Structure
* domain
  * models.py  (Placeholder for future domain models (e.g., PRs, issues))
  * service.py (Core crawling logic (business/domain layer))
* infrastructure
  * db
    * database.py (Database connection)
    * repository_repo.py (Database operations)
  * github
    * github_client.py (GitHub API client)
    * queries.py (GraphQL queries)
* scripts
  * setup_db.py (Database schema creation)
  * export_data.py (Export DB contents)
* src
  * app
    * config.py (Loads environment variables)
    * main.py (Entry point to run crawler)

### Rationale
* domain/services.py contains core business logic, independent of database or API.
* infrastructure contains external dependencies like GitHub API and DB.
* domain/models.py is unused now but reserved for future expansion (issues, PRs, commits, etc.).
* src/app/config.py loads all environment variables for DB and GitHub API tokens.

## Database Schema
Current schema (PostgreSQL, defined in infrastructure/db/migrations.sql):

To store additional metadata (issues, PRs, commits, comments, reviews, CI checks)
* Add separate tables: issues, pull_requests, commits, comments, reviews, ci_checks.
* Link to repositories via foreign keys.

## Crawling logic
* Fetch repositories incrementally based on star count ranges:
  * Start from 0 stars and increase dynamically.
  * Batch queries to respect GitHub API rate limits.
* Uses multi-threading for parallel API requests.
* Automatic retries on network failures.
* Logs progress at every 100 repositories.
* Example logs:
  * 2025-11-15 22:18:15,661 [INFO] crawler_service: Starting star range query: 'stars:0..499'
  * 2025-11-15 22:18:18,872 [INFO] crawler_service: Fetched 100/100000 repositories
  
## GitHub Actions Pipeline
1. PostgreSQL service container.
2. Setup & dependency installation (pip install -r requirements.txt).
3. Database setup (scripts/setup_db.py).
4. Crawl stars step (src/app/main.py) to fetch 100,000 repos.
5. Export step (scripts/export_data.py) to output CSV.

## How to Run
1. Set up .env with GitHub API token and PostgreSQL credentials.
2. Install dependencies: (pip install -r requirements.txt)
3. Setup the database: (python -m scripts.setup_db)
4. Run crawler: (python -m src.app.main)
5. Export results as CSV: (python -m scripts.export_data)

## Scaling Notes
If crawling 500 million repositories:
1. Distributed crawling
   1. Run multiple crawler instances in parallel.
   2. Each instance handles a different star range.
   3. Why it’s easy to explain: “We divide work across machines to finish faster.”
2. Persistent Cursors
   1. Store the last pagination cursor (or GraphQL page cursor) for each crawler job in the database (or a checkpoint table).
   2. With such a large scale, failures are expected. Restarting from zero every time would be wasteful.

## Schema Evolution
1. Current schema
   1. Repositories table with basic info: repo_id, full_name, stars.
   2. Updates are incremental: only rows that changed get updated.
2. Future tables for additional metadata
   1. issues, pull_requests, commits, comments, reviews, ci_checks.
   2. Each table references repo_id in repositories using a foreign key.
   3. Allows efficient updates: only new or modified rows are inserted/updated.
3. Incremental updates logic
   1. If a PR has 10 comments today and 20 tomorrow, only the 10 new comments are added.
   2. Only few rows will be effected.