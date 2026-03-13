"""
GitHub Scraper — uses public Search API (no auth = 10 req/min).
Finds trending repos, active hiring signals, and ecosystem shifts.
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from config import GITHUB_LANGUAGES, GITHUB_TRENDING_DAYS, GITHUB_MIN_STARS


def fetch_trending_repos(
    language: str | None = None,
    days: int = GITHUB_TRENDING_DAYS,
    min_stars: int = GITHUB_MIN_STARS,
    limit: int = 30,
) -> list[dict]:
    """Find repos created/updated recently with high star velocity."""
    date_since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    query_parts = [f"stars:>={min_stars}", f"pushed:>{date_since}"]
    if language:
        query_parts.append(f"language:{language}")
    query = " ".join(query_parts)

    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(limit, 30),
    })
    url = f"https://api.github.com/search/repositories?{params}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "NexScry/1.0",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠ GitHub search ({language}): {e}")
        return []

    repos = []
    for item in data.get("items", []):
        # Detect hiring signals
        desc = (item.get("description") or "").lower()
        topics = [t.lower() for t in item.get("topics", [])]
        hiring_signals = any(
            kw in desc or kw in " ".join(topics)
            for kw in ["hiring", "careers", "we're hiring", "job", "team"]
        )

        repos.append({
            "source": "github",
            "name": item.get("full_name"),
            "description": item.get("description", ""),
            "url": item.get("html_url"),
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "language": item.get("language"),
            "topics": item.get("topics", []),
            "open_issues": item.get("open_issues_count", 0),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "owner_type": item.get("owner", {}).get("type"),  # User vs Organization
            "hiring_signal": hiring_signals,
            "star_velocity": round(
                item.get("stargazers_count", 0) / max(days, 1), 1
            ),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    return repos


def fetch_repo_readme(full_name: str) -> str:
    """Fetch README content for deeper analysis."""
    url = f"https://api.github.com/repos/{full_name}/readme"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "NexScry/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="replace")[:3000]
    except Exception:
        return ""


def scrape_all() -> list[dict]:
    """Scrape trending repos across configured languages + general."""
    all_repos = []

    # General trending (all languages)
    print("  📡 GitHub: trending (all)...")
    all_repos.extend(fetch_trending_repos(language=None, limit=20))

    # Per-language trending
    for lang in GITHUB_LANGUAGES:
        print(f"  📡 GitHub: trending {lang}...")
        repos = fetch_trending_repos(language=lang, limit=15)
        all_repos.extend(repos)

    # Deduplicate by full_name
    seen = set()
    unique = []
    for r in all_repos:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append(r)

    unique.sort(key=lambda r: r["star_velocity"], reverse=True)
    print(f"  ✅ GitHub: {len(unique)} unique trending repos")
    return unique


if __name__ == "__main__":
    repos = scrape_all()
    for r in repos[:10]:
        hiring = " 🟢 HIRING" if r["hiring_signal"] else ""
        print(f"  ⭐{r['stars']} ({r['star_velocity']}/day) {r['name']}{hiring}")
