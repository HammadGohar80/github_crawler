import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from src.app.config import settings
from .queries import GET_REPOS_QUERY

class GitHubClient:

    def __init__(self, token: str):
        self.token = token

    @retry(stop=stop_after_attempt(settings.MAX_RETRIES), wait=wait_exponential(settings.RETRY_BACKOFF))
    def fetch_repositories(self, cursor=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"query": GET_REPOS_QUERY, "variables": {"cursor": cursor}}

        resp = requests.post(settings.GITHUB_API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()
