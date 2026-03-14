#!/usr/bin/env python3
"""
NexScry — AI-powered intelligence layer for builders.
Main pipeline: Scrape → Enrich → Cross-reference → Build site.

Usage:
  python main.py              # full pipeline
  python main.py --scrape     # scrape only (save raw data)
  python main.py --build      # build from existing data
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

from config import DATA_DIR, BUILD_DIR


def run_scrapers() -> dict:
    """Run all scrapers and return combined data."""
    print("\n🌐 PHASE 1: Scraping the open internet\n" + "=" * 50)

    all_data = {}

    # Reddit
    try:
        from scrapers.reddit import scrape_all as scrape_reddit
        all_data["reddit"] = scrape_reddit()
    except Exception as e:
        print(f"  ❌ Reddit scraper failed: {e}")
        all_data["reddit"] = []

    time.sleep(2)  # breathing room between sources

    # Hacker News
    try:
        from scrapers.hn import scrape_all as scrape_hn
        all_data["hackernews"] = scrape_hn()
    except Exception as e:
        print(f"  ❌ HN scraper failed: {e}")
        all_data["hackernews"] = []

    time.sleep(1)

    # GitHub
    try:
        from scrapers.github_trending import scrape_all as scrape_github
        all_data["github"] = scrape_github()
    except Exception as e:
        print(f"  ❌ GitHub scraper failed: {e}")
        all_data["github"] = []

    time.sleep(2)

    # ArXiv
    try:
        from scrapers.arxiv_scraper import scrape_all as scrape_arxiv
        all_data["arxiv"] = scrape_arxiv()
    except Exception as e:
        print(f"  ❌ ArXiv scraper failed: {e}")
        all_data["arxiv"] = []

    time.sleep(1)

    # Product Hunt
    try:
        from scrapers.producthunt import scrape_all as scrape_ph
        all_data["producthunt"] = scrape_ph()
    except Exception as e:
        print(f"  ❌ Product Hunt scraper failed: {e}")
        all_data["producthunt"] = []

    time.sleep(1)

    # DEV.to
    try:
        from scrapers.devto import scrape_all as scrape_devto
        all_data["devto"] = scrape_devto()
    except Exception as e:
        print(f"  ❌ DEV.to scraper failed: {e}")
        all_data["devto"] = []

    total = sum(len(v) for v in all_data.values())
    print(f"\n📊 Total scraped: {total} items from {len(all_data)} sources")
    return all_data


def run_processor(all_data: dict) -> dict:
    """Run AI enrichment + cross-source analysis."""
    print("\n🧠 PHASE 2: AI Processing (Groq)\n" + "=" * 50)

    from processor.groq_client import process_all
    return process_all(all_data)


def run_builder(processed_data: dict):
    """Generate static site."""
    print("\n🏗️ PHASE 3: Building site\n" + "=" * 50)

    from builder.templates import build_site
    build_site(processed_data)


def save_raw_data(all_data: dict):
    """Save raw scraped data for later processing."""
    os.makedirs(DATA_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(DATA_DIR, f"raw_{date_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Raw data saved to {filepath}")


def save_processed_data(processed_data: dict):
    """Save processed data."""
    os.makedirs(DATA_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(DATA_DIR, f"processed_{date_str}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Processed data saved to {filepath}")


def main():
    start = time.time()
    print("""
    ╔═══════════════════════════════════════════╗
    ║  NexScry — AI Intelligence for Builders   ║
    ║  Scrape → Enrich → Cross-ref → Publish    ║
    ╚═══════════════════════════════════════════╝
    """)

    mode = sys.argv[1] if len(sys.argv) > 1 else "--full"

    if mode == "--scrape":
        all_data = run_scrapers()
        save_raw_data(all_data)

    elif mode == "--build":
        # Load latest processed data
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filepath = os.path.join(DATA_DIR, f"processed_{date_str}.json")
        if not os.path.exists(filepath):
            print(f"❌ No processed data found at {filepath}")
            print("   Run full pipeline first: python main.py")
            sys.exit(1)
        with open(filepath, "r") as f:
            processed_data = json.load(f)
        run_builder(processed_data)

    else:  # --full (default)
        # Validate Groq API key upfront so we catch problems early
        from processor.groq_client import test_groq_connection
        api_ok = test_groq_connection()
        if not api_ok:
            print("\n  ⚠ AI enrichment will be skipped — set GROQ_API_KEY as a GitHub Secret")
            print("  ℹ  Scraped data will still be collected and the site will be built\n")

        all_data = run_scrapers()
        save_raw_data(all_data)
        processed_data = run_processor(all_data)
        save_processed_data(processed_data)
        run_builder(processed_data)

    elapsed = time.time() - start
    print(f"\n⚡ Done in {elapsed:.1f}s")
    print(f"🌐 Site ready at {BUILD_DIR}/index.html")


if __name__ == "__main__":
    main()
