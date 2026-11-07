#!/usr/bin/env python3
"""
Sync Kartik Sirohi's external open-source pull requests from the GitHub API.
Usage:
    python3 scripts/sync_prs.py
    python3 scripts/sync_prs.py --update-html
"""

import os
import sys
import json
import urllib.request
import urllib.error
import datetime
import html
import re

USERNAME = "sirohikartik"
QUERY = f"author:{USERNAME} type:pr -user:{USERNAME}"
API_URL = f"https://api.github.com/search/issues?q={urllib.parse.quote(QUERY)}&sort=created&order=desc"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT_DIR, "data", "prs.json")
INDEX_FILE = os.path.join(ROOT_DIR, "index.html")

def fetch_prs():
    headers = {"User-Agent": "Mozilla/5.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(API_URL, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("items", [])
    except urllib.error.HTTPError as e:
        print(f"Error fetching GitHub PRs: {e.code} {e.reason}", file=sys.stderr)
        if e.code == 403:
            print("Rate limit reached. Set GITHUB_TOKEN environment variable to increase limits.", file=sys.stderr)
        return []

def format_prs(raw_items):
    formatted = []
    for item in raw_items:
        repo = item["repository_url"].replace("https://api.github.com/repos/", "")
        is_merged = bool(item.get("pull_request", {}).get("merged_at"))
        state = "merged" if is_merged else item.get("state", "open")
        formatted.append({
            "number": item["number"],
            "repo": repo,
            "title": item["title"],
            "url": item["html_url"],
            "state": state,
            "created_at": item["created_at"]
        })
    return formatted

def time_ago(dt_str):
    now = datetime.datetime.now(datetime.timezone.utc)
    dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    diff = int((now - dt).total_seconds())
    if diff < 3600:
        return f"{max(1, diff // 60)}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    if diff < 2592000:
        return f"{diff // 86400}d ago"
    return f"{diff // 2592000}mo ago"

def main():
    print(f"Fetching open-source pull requests for {USERNAME}...")
    items = fetch_prs()
    if not items:
        print("No items fetched.")
        return

    prs = format_prs(items)
    print(f"Retrieved {len(prs)} pull requests.\n")

    # Terminal summary table
    print(f"{'STATE':<8} {'REPO':<28} {'PR':<8} {'TITLE':<45} {'TIME'}")
    print("-" * 100)
    for p in prs[:15]:
        st = f"[{p['state'].upper()}]"
        repo = p['repo'][:27]
        num = f"#{p['number']}"
        t = p['title'][:43]
        ago = time_ago(p['created_at'])
        print(f"{st:<8} {repo:<28} {num:<8} {t:<45} {ago}")

    # Save to data/prs.json
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(prs, f, indent=2)
    print(f"\nSaved {len(prs)} PRs to {DATA_FILE}")

if __name__ == "__main__":
    main()
