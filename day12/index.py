"""
Day 12 — GitHub PR Reviewer Agent (Ollama / local LLM version)
Usage: python index.py <PR_URL>
Example: python index.py https://github.com/owner/repo/pull/42
"""

import sys
import os
from dotenv import load_dotenv
from github_client import GitHubClient
from reviewer import PRReviewer

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: python index.py <PR_URL>")
        print("Example: python index.py https://github.com/owner/repo/pull/42")
        sys.exit(1)

    pr_url = sys.argv[1]
    post_comment = "--post" in sys.argv

    github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    reviewer = PRReviewer(github=github)

    print(f"\n Fetching PR: {pr_url}")
    review = reviewer.review_pr(pr_url)

    print("\n" + "=" * 60)
    print("REVIEW SUMMARY")
    print("=" * 60)
    print(review["summary"])

    print("\n" + "=" * 60)
    print("FILE COMMENTS")
    print("=" * 60)
    for comment in review["comments"]:
        print(f"\n {comment['file']}")
        print(f"   Severity : {comment['severity'].upper()}")
        print(f"   {comment['body']}")

    if not review["comments"]:
        print("\n No issues found — PR looks good!")

    if post_comment:
        print("\n Posting review to GitHub...")
        github.post_review(
            owner=review["owner"],
            repo=review["repo"],
            pr_number=review["pr_number"],
            body=review["summary"],
            comments=review["comments"]
        )
        print("Review posted!")
    else:
        print("\n Tip: Run with --post to automatically post this review to GitHub")


if __name__ == "__main__":
    main()
