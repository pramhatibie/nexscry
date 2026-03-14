"""
ArXiv Scraper — uses Atom feed API (fully open, no rate limits).
Fetches recent papers and extracts metadata for AI processing.
"""
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from config import ARXIV_CATEGORIES, ARXIV_MAX_PAPERS


ARXIV_API = "https://export.arxiv.org/api/query"


def _parse_atom_entries(xml_text: str) -> list[dict]:
    """Minimal Atom XML parser — no external deps needed."""
    entries = []
    # Split by <entry> tags
    raw_entries = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)

    for raw in raw_entries:
        def get_tag(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", raw, re.DOTALL)
            return m.group(1).strip() if m else ""

        def get_all_tag(tag):
            return re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", raw, re.DOTALL)

        arxiv_id_raw = get_tag("id")
        arxiv_id = arxiv_id_raw.split("/abs/")[-1] if "/abs/" in arxiv_id_raw else arxiv_id_raw

        # Extract categories
        categories = re.findall(r'<category[^>]*term="([^"]+)"', raw)

        # Extract authors
        authors = get_all_tag("name")

        entries.append({
            "source": "arxiv",
            "id": arxiv_id,
            "title": re.sub(r"\s+", " ", get_tag("title")),
            "summary": re.sub(r"\s+", " ", get_tag("summary"))[:1000],
            "authors": authors[:5],  # cap at 5
            "categories": categories,
            "primary_category": categories[0] if categories else "",
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            "published": get_tag("published"),
            "updated": get_tag("updated"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    return entries


def fetch_papers(
    categories: list[str] = ARXIV_CATEGORIES,
    max_results: int = ARXIV_MAX_PAPERS,
) -> list[dict]:
    """Fetch recent papers from specified ArXiv categories."""
    # Build query: cat:cs.AI OR cat:cs.LG OR ...
    cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
    params = urllib.parse.urlencode({
        "search_query": cat_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })

    url = f"{ARXIV_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "NexScry/1.0"})

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_text = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 15 * (attempt + 1)
                print(f"  ⏳ ArXiv rate-limited (429) — waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  ⚠ ArXiv HTTP {e.code}: {e}")
            return []
        except Exception as e:
            print(f"  ⚠ ArXiv: {e}")
            return []
    else:
        print(f"  ⚠ ArXiv: all attempts failed")
        return []

    papers = _parse_atom_entries(xml_text)
    print(f"  ✅ ArXiv: {len(papers)} papers fetched")
    return papers


def scrape_all() -> list[dict]:
    """Main entry point."""
    print("  📡 Scraping ArXiv...")
    return fetch_papers()


if __name__ == "__main__":
    papers = scrape_all()
    for p in papers[:10]:
        cats = ", ".join(p["categories"][:3])
        print(f"  [{cats}] {p['title'][:80]}")
