from src.app.config import settings
from infrastructure.github.github_client import GitHubClient
from domain.services import GitHubCrawlerService
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def main():
    client = GitHubClient(settings.GITHUB_ACCESS_TOKEN)

    crawler = GitHubCrawlerService(client, batch_size=settings.BATCH_SIZE, max_workers=settings.MAX_WORKERS)
    crawler.crawl_repos(total_repos=settings.TOTAL_REPOS, star_step=settings.STAR_STEP)

if __name__ == "__main__":
    main()