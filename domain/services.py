from models import Repository

class StarCrawlService:

    def __init__(self, repo_repo):
        self.repo_repo = repo_repo

    def process_repository(self, repo: Repository):
        self.repo_repo.upsert_repo(repo.repo_id, repo.full_name, repo.stars)
        self.repo_repo.insert_history(repo.repo_id, repo.stars)
