from infrastructure.github.github_client import GitHubClient
from infrastructure.db.repository_repo import RepositoryRepository
from domain.models import Repository
from domain.services import StarCrawlService
from src.app.config import settings

def run_crawler():

    token = "YOUR_GITHUB_DEFAULT_TOKEN"   # In GitHub Actions this comes auto
    client = GitHubClient(token)
    repo_repo = RepositoryRepository()
    service = StarCrawlService(repo_repo)

    cursor = None
    total = 0

    while total < 100000:

        data = client.fetch_repositories(cursor)
        edges = data["data"]["search"]["edges"]

        for e in edges:
            node = e["node"]

            repo = Repository(
                repo_id=int(node["id"].replace("R_", ""), 36) if "R_" in node["id"] else 0,
                full_name=node["nameWithOwner"],
                stars=node["stargazerCount"],
            )

            service.process_repository(repo)
            total += 1

            if total >= 100000:
                break

        cursor = data["data"]["search"]["pageInfo"]["endCursor"]
        if not data["data"]["search"]["pageInfo"]["hasNextPage"]:
            break

    print(f"Crawling complete: {total} repos processed.")
