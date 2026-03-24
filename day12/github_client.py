"""
GitHub API client — fetches PR metadata, diffs, and posts reviews.
"""

import re
import requests


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str):
        if not token:
            raise ValueError("GITHUB_TOKEN is required. Get one at https://github.com/settings/tokens")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def parse_pr_url(self, url: str) -> tuple[str, str, int]:
        """Extract owner, repo, PR number from a GitHub PR URL."""
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
        if not match:
            raise ValueError(f"Invalid PR URL: {url}")
        owner, repo, number = match.groups()
        return owner, repo, int(number)

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        """Fetch PR metadata."""
        url = f"{self.BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch list of changed files with their patches (diffs)."""
        url = f"{self.BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        resp = requests.get(url, headers=self.headers, params={"per_page": 50})
        resp.raise_for_status()
        return resp.json()

    def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        """Fetch commits in the PR."""
        url = f"{self.BASE}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def post_review(self, owner: str, repo: str, pr_number: int, body: str, comments: list[dict]):
        """Post a review with inline comments to GitHub."""
        url = f"{self.BASE}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"

        inline = []
        for c in comments:
            if c.get("line"):
                inline.append({
                    "path": c["file"],
                    "line": c["line"],
                    "body": f"**[{c['severity'].upper()}]** {c['body']}"
                })

        payload = {
            "body": body,
            "event": "COMMENT",
            "comments": inline
        }

        resp = requests.post(url, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()
