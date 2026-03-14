"""
Reddit Scraper — uses public JSON endpoints (no API key needed).
Reddit exposes .json on every page. GitHub Actions runs from US servers,
so no ISP blocks affect this.
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from config import REDDIT_SUBS, REDDIT_SORT, REDDIT_LIMIT, REDDIT_PAIN_KEYWORDS


# Reddit requires a descriptive User-Agent to avoid 429/403
USER_AGENT = "Mozilla/5.0 (compatible; NexScry/1.0; +https://github.com/pramhatibie/nexscry)"


def fetch_subreddit(sub: str, sort: str = REDDIT_SORT, limit: int = REDDIT_LIMIT) -> list[dict]:
    """Fetch posts from a subreddit's public JSON feed."""
    url = f"https://www.reddit.com/r/{sub}/{sort}.json?limit={limit}&raw_json=1"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })

    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)
                break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  ⏳ r/{sub}: rate-limited (429) — waiting 15s...")
                time.sleep(15)
                continue
            if e.code == 403:
                print(f"  ⚠ r/{sub}: 403 Forbidden — Reddit may be blocking this IP. Trying old.reddit.com...")
                # Fallback to old.reddit.com which is less aggressive
                url = f"https://old.reddit.com/r/{sub}/{sort}.json?limit={limit}&raw_json=1"
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=20) as resp2:
                        data = json.loads(resp2.read().decode("utf-8", errors="replace"))
                    break
                except Exception as e2:
                    print(f"  ⚠ r/{sub} old.reddit fallback failed: {e2}")
                    return []
            print(f"  ⚠ r/{sub}: HTTP {e.code} — {e}")
            return []
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"  ⚠ r/{sub}: {e}")
            return []
    else:
        print(f"  ⚠ r/{sub}: all attempts failed")
        return []

    posts = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        if not d.get("title"):
            continue

        # Extract pain signals from title + selftext
        text_blob = f"{d.get('title', '')} {d.get('selftext', '')[:500]}".lower()
        pain_matches = [kw for kw in REDDIT_PAIN_KEYWORDS if kw.lower() in text_blob]

        posts.append({
            "source": "reddit",
            "sub": sub,
            "id": d.get("id"),
            "title": d.get("title", ""),
            "selftext": (d.get("selftext", "") or "")[:1000],
            "url": f"https://reddit.com{d.get('permalink', '')}",
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "created_utc": d.get("created_utc", 0),
            "author": d.get("author", "[deleted]"),
            "pain_signals": pain_matches,
            "has_pain": len(pain_matches) > 0,
            "flair": d.get("link_flair_text", ""),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    return posts


def fetch_comments_for_post(post_id: str, sub: str, limit: int = 20) -> list[dict]:
    """Fetch top comments for a specific post (for deep analysis)."""
    url = f"https://www.reddit.com/r/{sub}/comments/{post_id}.json?limit={limit}&raw_json=1"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    comments = []
    if len(data) > 1:
        for child in data[1].get("data", {}).get("children", []):
            d = child.get("data", {})
            body = d.get("body", "")
            if body and d.get("author") != "AutoModerator":
                comments.append({
                    "body": body[:500],
                    "score": d.get("score", 0),
                    "author": d.get("author", ""),
                })
    return comments


def scrape_all() -> list[dict]:
    """Scrape all configured subreddits. Returns flat list of posts."""
    all_posts = []
    for sub in REDDIT_SUBS:
        print(f"  📡 Scraping r/{sub}...")
        posts = fetch_subreddit(sub)
        all_posts.extend(posts)
        time.sleep(1.5)  # polite rate limiting

    # Sort by engagement (score * comments gives weight to discussion)
    all_posts.sort(key=lambda p: p["score"] * max(p["num_comments"], 1), reverse=True)

    print(f"  ✅ Reddit: {len(all_posts)} posts from {len(REDDIT_SUBS)} subs")
    return all_posts


if __name__ == "__main__":
    posts = scrape_all()
    pain_posts = [p for p in posts if p["has_pain"]]
    print(f"\n🔥 Pain signal posts: {len(pain_posts)}/{len(posts)}")
    for p in pain_posts[:5]:
        print(f"  [{p['sub']}] {p['title'][:80]}  (signals: {p['pain_signals']})")
