"""
PR Reviewer Agent — uses local Ollama (qwen2.5:7b) to review each changed file.

Agent loop:
  for each file in PR:
    → reason about the diff (Ollama)
    → produce structured JSON feedback
  → aggregate all feedback
  → produce final summary (Ollama)
"""

import json
import re
import os
from openai import OpenAI
from prompts import SYSTEM_PROMPT, FILE_REVIEW_PROMPT, FINAL_SUMMARY_PROMPT

# Files to skip — diffs in these are rarely useful to review
SKIP_EXTENSIONS = {
    ".lock", ".sum", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".min.js", ".min.css"
}

# Max diff size per file to avoid blowing the context window
MAX_PATCH_CHARS = 6000

# Ollama model to use — change this if you want to try a different model
OLLAMA_MODEL = "qwen2.5:7b"


class PRReviewer:
    def __init__(self, github):
        self.github = github
        # Point OpenAI client to local Ollama server
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"  # Ollama does not require a real key
        )

    def review_pr(self, pr_url: str) -> dict:
        # Step 1: Parse URL and fetch PR metadata
        owner, repo, pr_number = self.github.parse_pr_url(pr_url)
        print(f"   Owner: {owner} | Repo: {repo} | PR: #{pr_number}")

        pr = self.github.get_pr(owner, repo, pr_number)
        files = self.github.get_pr_files(owner, repo, pr_number)

        print(f"   Title: {pr['title']}")
        print(f"   Author: {pr['user']['login']}")
        print(f"   Files changed: {len(files)}")

        # Step 2: Review each file
        file_reviews = []
        comments = []

        reviewable = [f for f in files if self._should_review(f)]
        print(f"\n   Reviewing {len(reviewable)} files (skipping binaries/lockfiles)...\n")

        for i, file in enumerate(reviewable):
            filename = file["filename"]
            print(f"   [{i+1}/{len(reviewable)}] Reviewing {filename}...")

            review = self._review_file(
                filename=filename,
                patch=file.get("patch", ""),
                status=file.get("status", "modified"),
                additions=file.get("additions", 0),
                deletions=file.get("deletions", 0),
                pr_title=pr["title"],
                pr_description=pr.get("body") or "No description provided"
            )

            file_reviews.append({
                "file": filename,
                "summary": review.get("summary", ""),
                "issues": review.get("issues", []),
                "looks_good": review.get("looks_good", True)
            })

            for issue in review.get("issues", []):
                comments.append({
                    "file": filename,
                    "severity": issue.get("severity", "style"),
                    "line": issue.get("line"),
                    "body": issue["comment"]
                })

        # Step 3: Generate overall summary
        print("\n   Generating final review summary...")
        summary = self._generate_summary(
            pr_title=pr["title"],
            pr_author=pr["user"]["login"],
            files_changed=len(files),
            additions=pr["additions"],
            deletions=pr["deletions"],
            file_reviews=file_reviews
        )

        return {
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "summary": summary,
            "comments": comments,
            "file_reviews": file_reviews
        }

    def _should_review(self, file: dict) -> bool:
        """Skip files that are not worth reviewing."""
        filename = file.get("filename", "")
        if not file.get("patch"):
            return False
        for ext in SKIP_EXTENSIONS:
            if filename.endswith(ext):
                return False
        if file.get("status") == "removed":
            return False
        return True

    def _review_file(self, filename, patch, status, additions, deletions, pr_title, pr_description) -> dict:
        """Ask Ollama to review a single file diff."""
        if len(patch) > MAX_PATCH_CHARS:
            patch = patch[:MAX_PATCH_CHARS] + f"\n\n[... diff truncated at {MAX_PATCH_CHARS} chars ...]"

        prompt = FILE_REVIEW_PROMPT.format(
            pr_title=pr_title,
            pr_description=pr_description,
            filename=filename,
            status=status,
            additions=additions,
            deletions=deletions,
            patch=patch
        )

        response = self.client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )

        raw = response.choices[0].message.content.strip()
        return self._parse_json(raw)

    def _generate_summary(self, pr_title, pr_author, files_changed, additions, deletions, file_reviews) -> str:
        """Generate the overall PR review summary."""
        reviews_text = ""
        for r in file_reviews:
            reviews_text += f"\n{r['file']}:\n"
            reviews_text += f"  Summary: {r['summary']}\n"
            if r["issues"]:
                for issue in r["issues"]:
                    reviews_text += f"  - [{issue['severity']}] {issue['comment']}\n"
            else:
                reviews_text += "  - No issues found\n"

        prompt = FINAL_SUMMARY_PROMPT.format(
            pr_title=pr_title,
            pr_author=pr_author,
            files_changed=files_changed,
            additions=additions,
            deletions=deletions,
            file_reviews=reviews_text
        )

        response = self.client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content.strip()

    def _parse_json(self, raw: str) -> dict:
        """
        Robustly parse JSON from model output.
        Local models sometimes wrap JSON in markdown or add extra text.
        """
        # Try direct parse first
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Extract first {...} block
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Final fallback
        print(f"   Warning: Could not parse JSON from model output. Raw: {raw[:100]}")
        return {
            "issues": [],
            "looks_good": True,
            "summary": raw[:200]
        }
