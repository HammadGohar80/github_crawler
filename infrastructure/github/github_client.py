import requests
import time
import random
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from src.app.config import settings

logger = logging.getLogger("github_client")
logger.setLevel(logging.INFO)


class GitHubClient:
    def __init__(
        self,
        token: Optional[str] = None,
        api_url: Optional[str] = None,
        max_retries: Optional[int] = None,
        backoff_base: Optional[int] = None,
        rate_limit_threshold: int = 50,
    ):
        self.token = token or getattr(settings, "GITHUB_ACCESS_TOKEN", None)
        if not self.token:
            raise ValueError("GitHub access token is required (GITHUB_ACCESS_TOKEN).")

        self.api_url = api_url or getattr(settings, "GITHUB_API_URL", "https://api.github.com/graphql")
        self.max_retries = max_retries or getattr(settings, "MAX_RETRIES", 5)
        self.backoff_base = backoff_base or getattr(settings, "RETRY_BACKOFF", 2)
        # If remaining points drop below this threshold, wait until resetAt
        self.rate_limit_threshold = rate_limit_threshold

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v4+json",
            "User-Agent": "github-crawler/1.0",
        }

    def _seconds_until_reset(self, reset_at_iso: str) -> float:
        """
        Parse ISO timestamp from GitHub like '2025-11-15T14:47:10Z' and return seconds until reset.
        If parsing fails, return a conservative 60 seconds.
        """
        try:
            # github returns ZULU time
            dt = datetime.strptime(reset_at_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            seconds = (dt - now).total_seconds()
            return max(0.0, seconds)
        except Exception as e:
            logger.warning("Failed to parse resetAt '%s': %s", reset_at_iso, e)
            return 60.0

    def _maybe_handle_rate_limit(self, payload: Dict[str, Any]) -> None:
        """
        Inspect payload for rateLimit info and sleep until reset if remaining is too low.
        Expects payload to be the parsed JSON from the GraphQL response.
        """
        try:
            rate = payload.get("data", {}).get("rateLimit")
            if not rate:
                return

            remaining = rate.get("remaining")
            reset_at = rate.get("resetAt")
            if remaining is None or reset_at is None:
                return

            # If remaining points are below threshold, wait until resetAt
            if int(remaining) <= self.rate_limit_threshold:
                wait_sec = self._seconds_until_reset(reset_at) + 1.0  # small buffer
                logger.info("Rate limit low (remaining=%s). Sleeping %.0f seconds until resetAt=%s",
                            remaining, wait_sec, reset_at)
                time.sleep(wait_sec)
        except Exception:
            # never let rate-limit handling throw unhandled exceptions
            logger.exception("Error while handling rate limit info; continuing.")

    def run_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a GraphQL query with retries and rate-limit handling.
        Returns the parsed JSON response (may contain 'data' or 'errors').
        Raises requests.HTTPError after exhausting retries for non-200 responses.
        Raises Exception if retries exhausted for other cases.
        """
        variables = variables or {}
        attempt = 0
        last_exception = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                logger.debug("GraphQL request attempt %d; variables=%s", attempt, {k: v for k, v in variables.items() if k != "token"})
                resp = requests.post(self.api_url, json={"query": query, "variables": variables}, headers=self.headers, timeout=30)

                # HTTP errors (non-200) -> retry with backoff
                if resp.status_code != 200:
                    logger.warning("GitHub HTTP %s on attempt %d: %s", resp.status_code, attempt, resp.text[:400])
                    status = resp.status_code
                    # 4xx (except 429) are likely client errors; still retry a few times for transient auth blips
                    # 5xx are server errors --> retry
                    backoff_ms = min(120000, self.backoff_base * 1000 * 2 ** (attempt - 1)) + random.randint(0, 1000)
                    backoff_s = backoff_ms / 1000.0
                    logger.info("Backing off %.1f s (attempt %d/%d) after HTTP %s", backoff_s, attempt, self.max_retries, status)
                    time.sleep(backoff_s)
                    last_exception = requests.HTTPError(f"HTTP {status}: {resp.text}")
                    continue

                payload = resp.json()

                # If GraphQL-level errors present, log them and decide whether to retry
                if "errors" in payload:
                    # If error is related to complexity/cost or server, backoff and retry
                    logger.warning("GraphQL errors on attempt %d: %s", attempt, payload.get("errors"))
                    # If errors look like rate limiting or abuse, inspect rateLimit in payload first
                    self._maybe_handle_rate_limit(payload)

                    # Backoff then retry
                    backoff_ms = min(120000, self.backoff_base * 1000 * 2 ** (attempt - 1)) + random.randint(0, 1000)
                    time.sleep(backoff_ms / 1000.0)
                    last_exception = Exception(f"GraphQL errors: {payload.get('errors')}")
                    continue

                # handle rate-limit proactively (if remaining low, it'll sleep)
                self._maybe_handle_rate_limit(payload)

                # success
                return payload

            except requests.RequestException as e:
                # network-level errors (timeouts, connection errors)
                logger.warning("RequestException on attempt %d: %s", attempt, str(e))
                backoff_ms = min(120000, self.backoff_base * 1000 * 2 ** (attempt - 1)) + random.randint(0, 1000)
                time.sleep(backoff_ms / 1000.0)
                last_exception = e
                continue
            except Exception as e:
                # catch-all: if it's the last attempt, rethrow after logging
                logger.exception("Unexpected error while running GraphQL query (attempt %d): %s", attempt, e)
                last_exception = e
                backoff_ms = min(120000, self.backoff_base * 1000 * 2 ** (attempt - 1)) + random.randint(0, 1000)
                time.sleep(backoff_ms / 1000.0)
                continue

        # exhausted retries
        logger.error("Exhausted %d attempts for query. Raising last exception.", self.max_retries)
        if last_exception:
            raise last_exception
        raise RuntimeError("GraphQL query failed for unknown reason.")
