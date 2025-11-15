import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from infrastructure.db.database import get_connection
from infrastructure.github.queries import GET_REPOS_QUERY
from infrastructure.github.github_client import GitHubClient
from psycopg2.extras import execute_values

logger = logging.getLogger("crawler_service")
logger.setLevel(logging.INFO)


class GitHubCrawlerService:
    def __init__(self, client: GitHubClient, batch_size=100, max_workers=10):
        self.client = client
        self.batch_size = batch_size
        self.max_workers = max_workers

    def crawl_repos(self, total_repos=10000, star_step=500):
        """
        Crawl repositories incrementally by increasing star ranges from 0 until total_repos are fetched.
        """
        logger.info(f"Starting incremental crawl for {total_repos} repositories")
        fetched = 0
        min_star = 0
        max_star = star_step - 1

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while fetched < total_repos:
                star_query = f"stars:{min_star}..{max_star}" if min_star > 0 else f"stars:0..{max_star}"
                logger.info(f"Starting star range query: '{star_query}'")

                after_cursor = None
                futures = []

                # submit first batch
                remaining = min(self.batch_size, total_repos - fetched)
                variables = {"query": star_query, "first": remaining, "after": after_cursor}
                futures.append(executor.submit(self.client.run_query, GET_REPOS_QUERY, variables))

                while futures and fetched < total_repos:
                    for future in as_completed(futures):
                        try:
                            data = future.result()
                            nodes = data["data"]["search"]["nodes"]
                            page_info = data["data"]["search"]["pageInfo"]
                            after_cursor = page_info["endCursor"]

                            if not nodes:
                                continue

                            self.save_to_db(nodes)
                            fetched += len(nodes)
                            logger.info(f"Fetched {fetched}/{total_repos} repositories")

                            # If more pages exist in current star range, submit next batch
                            if page_info["hasNextPage"] and fetched < total_repos:
                                remaining = min(self.batch_size, total_repos - fetched)
                                variables = {"query": star_query, "first": remaining, "after": after_cursor}
                                futures.append(executor.submit(self.client.run_query, GET_REPOS_QUERY, variables))

                        except Exception as e:
                            logger.exception(f"Error fetching batch: {e}")

                    futures = [f for f in futures if not f.done()]

                # move to next higher star range
                min_star = max_star + 1
                max_star = min_star + star_step - 1

        logger.info(f"Crawl finished. Total repositories fetched: {fetched}")

    def save_to_db(self, nodes):
        if not nodes:
            return

        conn = get_connection()
        cursor = conn.cursor()

        # Batch insert for repositories
        repo_values = [
            (node["databaseId"], f"{node['owner']['login']}/{node['name']}", node["stargazerCount"])
            for node in nodes
        ]
        execute_values(cursor, """
            INSERT INTO repositories (repo_id, full_name, stars)
            VALUES %s
            ON CONFLICT (repo_id) DO UPDATE SET
                stars = EXCLUDED.stars,
                last_crawled = NOW()
        """, repo_values)

        # Batch insert for stars_history
        stars_values = [
            (node["databaseId"], node["stargazerCount"])
            for node in nodes
        ]
        execute_values(cursor, """
            INSERT INTO stars_history (repo_id, stars)
            VALUES %s
        """, stars_values)

        conn.commit()
        cursor.close()
        conn.close()
