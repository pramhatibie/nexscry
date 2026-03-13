# NexScry — AI-Powered Intelligence Layer for Builders

> Scrapes the open internet. Cross-references signals across 6 platforms.  
> Distills them into actionable intelligence. Updated daily. Powered by Groq.

**Live:** [nexscry.xyz](https://nexscry.xyz)

---

## What Makes This Different

Most "AI aggregators" just summarize. NexScry does **cross-source intelligence**:

- A Reddit user complains about X → GitHub repo solving X starts trending → ArXiv paper about X drops this week
- Product Hunt launch in niche Y → r/SaaS thread asking for Y → DEV.to tutorial about Y gets 500+ reactions

NexScry catches these **convergence signals** automatically using Groq's inference speed. By the time you read your morning coffee brief, NexScry has already processed 500+ data points across 6 platforms.

---

## Data Sources (All Free, All Public)

| Source | API/Method | Auth Required | Rate Limit |
|--------|-----------|---------------|------------|
| Reddit | Public `.json` endpoints | No | ~60 req/min |
| Hacker News | Algolia API | No | Unlimited |
| GitHub | Search API | No (10 req/min) | Sufficient for daily |
| ArXiv | Atom feed | No | Unlimited |
| Product Hunt | RSS feed | No | Unlimited |
| DEV.to | Public API | No | Unlimited |

---

## Tech Stack (Zero Cost)

- **Scraping:** Python stdlib only (`urllib`, `json`, `re`) — no pip installs
- **AI Processing:** Groq Free Tier (llama-3.3-70b-versatile)
- **Automation:** GitHub Actions (free for public repos, unlimited minutes)
- **Hosting:** GitHub Pages (free, global CDN)
- **Database:** Git itself (JSON files committed daily, version history = time machine)
- **Domain:** ~$2/year for .xyz

**Total infrastructure cost: $0/month + ~$2/year for domain**

---

## Setup (15 minutes, seriously)

### Step 1: Get a Groq API Key (free)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free, no credit card)
3. Go to API Keys → Create new key
4. Copy the key — you'll need it in Step 4

### Step 2: Create GitHub Repository
1. Go to [github.com/new](https://github.com/new)
2. Name: `nexscry` (or whatever you want)
3. **IMPORTANT:** Make it **Public** (needed for free GitHub Actions + Pages)
4. Don't initialize with README (we'll push our own)

### Step 3: Push This Code
```bash
# In terminal, go to where you extracted the zip
cd nexscry

# Initialize git and push
git init
git add .
git commit -m "🚀 Initial NexScry setup"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nexscry.git
git push -u origin main
```

### Step 4: Add Groq API Key as Secret
1. Go to your repo on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `GROQ_API_KEY`
5. Value: paste your Groq API key
6. Click "Add secret"

### Step 5: Enable GitHub Pages
1. Go to repo Settings → Pages
2. Source: **GitHub Actions**
3. That's it — the workflow handles deployment

### Step 6: Set Up Custom Domain (optional)
1. Buy `nexscry.xyz` on [Porkbun](https://porkbun.com) (~$2/year)
2. In Porkbun DNS settings, add:
   - Type: `CNAME`, Host: `@`, Answer: `YOUR_USERNAME.github.io`
   - Type: `CNAME`, Host: `www`, Answer: `YOUR_USERNAME.github.io`
3. In GitHub repo Settings → Pages → Custom domain: `nexscry.xyz`
4. Check "Enforce HTTPS"

### Step 7: First Run
1. Go to your repo → Actions tab
2. Click "NexScry Daily Pipeline" → "Run workflow" → "Run workflow"
3. Wait 5-10 minutes
4. Check the Pages URL or nexscry.xyz — your site is live!

---

## Project Structure

```
nexscry/
├── .github/workflows/
│   └── daily.yml           # Cron job: runs at 06:00 UTC daily
├── scrapers/
│   ├── reddit.py           # Reddit public JSON scraper
│   ├── hn.py               # Hacker News Algolia API
│   ├── github_trending.py  # GitHub trending repos
│   ├── arxiv_scraper.py    # ArXiv paper feed
│   ├── producthunt.py      # Product Hunt RSS
│   └── devto.py            # DEV.to public API
├── processor/
│   └── groq_client.py      # AI enrichment + cross-source intelligence
├── builder/
│   └── templates.py        # Static site generator
├── data/                   # Auto-generated: raw + processed JSON
├── docs/                   # Auto-generated: static site (GitHub Pages)
├── config.py               # All settings in one place
├── main.py                 # Pipeline orchestrator
└── README.md
```

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                 GitHub Actions (daily)                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. SCRAPE          2. ENRICH           3. BUILD     │
│  ┌──────────┐      ┌──────────┐       ┌──────────┐  │
│  │ Reddit   │──┐   │ Per-item │       │ Static   │  │
│  │ HN       │  │   │ analysis │──┐    │ HTML     │  │
│  │ GitHub   │──┼──▶│ (Groq)   │  │    │ site     │  │
│  │ ArXiv    │  │   │          │  ├───▶│ with     │  │
│  │ PH       │  │   │ Cross-   │  │    │ SEO      │  │
│  │ DEV.to   │──┘   │ source   │──┘    │ pages    │  │
│  └──────────┘      │ signals  │       └────┬─────┘  │
│                    └──────────┘            │         │
│                                           ▼         │
│                                    GitHub Pages     │
│                                    (nexscry.xyz)    │
└─────────────────────────────────────────────────────┘
```

---

## Customization

### Add/Remove Subreddits
Edit `config.py` → `REDDIT_SUBS` list.

### Change AI Model
Edit `config.py` → `GROQ_MODEL`. Options:
- `llama-3.3-70b-versatile` (best quality, default)
- `llama-3.1-8b-instant` (faster, less accurate — used as fallback)
- `mixtral-8x7b-32768` (good middle ground)

### Add New Data Source
1. Create `scrapers/your_source.py` with a `scrape_all()` function
2. Add enrichment function in `processor/groq_client.py`
3. Import and call in `main.py`
4. Add source styling in `builder/templates.py`

---

## SEO Strategy

NexScry auto-generates SEO value through:
- **Daily-fresh content** (Google rewards update frequency)
- **Long-tail keywords** (every paper title, repo name, Reddit thread = unique landing page)
- **Structured data** ready for rich snippets
- **Cross-source narratives** that create unique content Google can't find elsewhere

---

## License

MIT — do whatever you want with it.
