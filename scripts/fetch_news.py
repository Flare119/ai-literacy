#!/usr/bin/env python3
"""
fetch_news.py — Daily AI news digest for AI Literacy tab.

Sources:
  - Brave Search API (web)
  - Reddit JSON public API (no auth)
  - HackerNews API (no auth)

Pipeline:
  1. Fetch raw articles from sources
  2. Dedupe + filter
  3. Gemini Flash: categorize + summarize each article
  4. Claude Sonnet: write weekly insight (only on Sunday)
  5. Output news.json + archive

Run: python3 fetch_news.py
Env vars required:
  BRAVE_API_KEY
  GEMINI_API_KEY
  ANTHROPIC_API_KEY  (optional, for weekly insight)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────
BRAVE_KEY = os.environ.get("BRAVE_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

ROOT = Path(__file__).resolve().parent.parent
NEWS_DIR = ROOT / "news"

TZ_SAIGON = timezone(timedelta(hours=7))
NOW = datetime.now(TZ_SAIGON)
DATE_STR = NOW.strftime("%Y-%m-%d")
IS_SUNDAY = NOW.weekday() == 6  # Mon=0, Sun=6

# ── Brave queries (open-ended for max coverage) ──
BRAVE_QUERIES = [
    ("ai_news", '"AI" OR "artificial intelligence" news', "week"),
    ("models", "new AI model released OR launch", "week"),
    ("agents", "AI agent OR coding agent OR computer-use", "week"),
    ("video_image", "AI video OR image model release", "week"),
    ("funding", "AI startup funding OR acquisition", "week"),
    ("tools", "new AI tool launch OR feature release", "week"),
    ("vietnam", "AI Vietnam OR VinAI OR FPT OR Zalo", "month"),
]

# Reddit subs to scan
REDDIT_SUBS = [
    "StableDiffusion",
    "HiggsfieldAI",
    "ChatGPT",
    "ClaudeAI",
    "LocalLLaMA",
    "singularity",
    "artificial",
    "MachineLearning",
]

# Tier 1 RSS feeds (authoritative real-time AI news)
RSS_FEEDS = [
    ("techcrunch_ai", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("verge_ai", "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
    ("arstechnica_ai", "https://arstechnica.com/ai/feed/"),
    ("venturebeat_ai", "https://venturebeat.com/category/ai/feed/"),
    ("mit_tech_review", "https://www.technologyreview.com/feed/"),
    ("arxiv_cs_ai", "http://export.arxiv.org/rss/cs.AI"),
]

# Vietnam tech RSS
VN_RSS = [
    ("vnexpress_tech", "https://vnexpress.net/rss/so-hoa.rss"),
    ("genk", "https://genk.vn/rss/home.rss"),
]

HEADERS = {
    "User-Agent": "AILiteracyNewsBot/1.0 (+https://flare119.github.io/ai-literacy)"
}


def http_get(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers=headers or HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def http_post(url, data, headers=None, timeout=60):
    req = urllib.request.Request(
        url, data=json.dumps(data).encode("utf-8"),
        headers=headers or {"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


# ── Fetch sources ──────────────────────────────

def fetch_brave(query, freshness="week", count=10):
    if not BRAVE_KEY:
        print("  [skip] no BRAVE_API_KEY")
        return []
    params = {
        "q": query[:400],  # Brave query max 400 chars
        "count": count,
        "freshness": "pw" if freshness == "week" else "pm",
    }
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(params)
    headers = {"X-Subscription-Token": BRAVE_KEY, "Accept": "application/json"}
    try:
        data = json.loads(http_get(url, headers=headers))
        results = data.get("web", {}).get("results", [])
        return [{
            "title": r.get("title", "").strip(),
            "url": r.get("url", ""),
            "snippet": r.get("description", "").strip(),
            "source": r.get("profile", {}).get("name", "") or r.get("meta_url", {}).get("hostname", ""),
            "published": r.get("page_age", ""),
            "_origin": "brave"
        } for r in results]
    except Exception as e:
        print(f"  [err] brave {query}: {e}")
        return []


def fetch_reddit(sub, limit=15):
    url = f"https://www.reddit.com/r/{sub}/top.json?t=day&limit={limit}"
    try:
        data = json.loads(http_get(url))
        posts = data.get("data", {}).get("children", [])
        results = []
        for p in posts:
            d = p.get("data", {})
            if d.get("score", 0) < 50:
                continue  # filter low-quality
            results.append({
                "title": d.get("title", "").strip(),
                "url": d.get("url", ""),
                "snippet": (d.get("selftext", "") or "")[:300],
                "source": f"r/{sub}",
                "published": datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat(),
                "score": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "_origin": "reddit"
            })
        return results
    except Exception as e:
        print(f"  [err] reddit r/{sub}: {e}")
        return []


def fetch_rss(name, url, limit=10, ai_filter=False):
    """Fetch RSS/Atom feed. Pure stdlib XML parser."""
    import xml.etree.ElementTree as ET
    try:
        raw = http_get(url, timeout=20)
        root = ET.fromstring(raw)
        # Strip namespaces
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]
        items = root.findall('.//item') or root.findall('.//entry')
        results = []
        ai_keywords = ["ai", "artificial intelligence", "machine learning", "llm", "gpt",
                       "claude", "gemini", "anthropic", "openai", "model", "chatbot",
                       "neural", "deep learning", "agent", "trí tuệ nhân tạo"]
        for it in items[:limit * 3]:
            title = (it.findtext('title') or "").strip()
            link = (it.findtext('link') or "").strip()
            if not link:
                link_el = it.find('link')
                if link_el is not None:
                    link = link_el.get('href', '') or (link_el.text or '')
            desc = (it.findtext('description') or it.findtext('summary') or "").strip()
            # Strip HTML tags from desc
            import re
            desc = re.sub(r'<[^>]+>', '', desc)[:400]
            pub = (it.findtext('pubDate') or it.findtext('published') or "").strip()
            if not title or not link:
                continue
            if ai_filter:
                blob = (title + " " + desc).lower()
                if not any(k in blob for k in ai_keywords):
                    continue
            results.append({
                "title": title,
                "url": link,
                "snippet": desc,
                "source": name.replace("_", " ").title(),
                "published": pub,
                "_origin": "rss"
            })
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        print(f"  [err] rss {name}: {e}")
        return []


def fetch_huggingface_papers(limit=10):
    """HuggingFace daily papers — research highlights."""
    try:
        data = json.loads(http_get("https://huggingface.co/api/daily_papers", timeout=20))
        results = []
        for p in data[:limit]:
            paper = p.get("paper", {})
            title = paper.get("title", "")
            url = f"https://huggingface.co/papers/{paper.get('id', '')}"
            summary = paper.get("summary", "")[:400]
            results.append({
                "title": title,
                "url": url,
                "snippet": summary,
                "source": "HuggingFace Papers",
                "published": paper.get("publishedAt", ""),
                "score": paper.get("upvotes", 0),
                "_origin": "huggingface"
            })
        return results
    except Exception as e:
        print(f"  [err] huggingface: {e}")
        return []


def fetch_github_trending_ai(limit=10):
    """GitHub trending AI repos via search API (no auth needed)."""
    try:
        # Repos with AI topics, recently updated, sorted by stars
        from datetime import timedelta as td
        since = (NOW - td(days=7)).strftime("%Y-%m-%d")
        url = f"https://api.github.com/search/repositories?q=topic:ai+pushed:>{since}&sort=stars&order=desc&per_page={limit}"
        data = json.loads(http_get(url, headers={**HEADERS, "Accept": "application/vnd.github+json"}))
        results = []
        for r in data.get("items", [])[:limit]:
            results.append({
                "title": f"{r['full_name']}: {r.get('description', '')[:120]}",
                "url": r.get("html_url", ""),
                "snippet": r.get("description", "")[:300] + f" · ⭐ {r.get('stargazers_count', 0)} · {r.get('language', '')}",
                "source": "GitHub Trending",
                "published": r.get("updated_at", ""),
                "score": r.get("stargazers_count", 0),
                "_origin": "github"
            })
        return results
    except Exception as e:
        print(f"  [err] github: {e}")
        return []


def fetch_hackernews(limit=20):
    try:
        ids = json.loads(http_get("https://hacker-news.firebaseio.com/v0/topstories.json"))[:50]
        results = []
        for hid in ids:
            try:
                item = json.loads(http_get(f"https://hacker-news.firebaseio.com/v0/item/{hid}.json"))
                title = (item.get("title") or "").lower()
                if not any(k in title for k in ["ai", "llm", "gpt", "claude", "gemini", "model", "agent", "anthropic", "openai", "deepseek", "llama"]):
                    continue
                if item.get("score", 0) < 100:
                    continue
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={hid}"),
                    "snippet": "",
                    "source": "Hacker News",
                    "published": datetime.fromtimestamp(item.get("time", 0), tz=timezone.utc).isoformat(),
                    "score": item.get("score", 0),
                    "comments": item.get("descendants", 0),
                    "_origin": "hackernews"
                })
                if len(results) >= limit:
                    break
            except Exception:
                continue
        return results
    except Exception as e:
        print(f"  [err] hackernews: {e}")
        return []


# ── Dedup + filter ──────────────────────────────

def dedupe(articles):
    seen_urls = set()
    seen_titles = set()
    out = []
    for a in articles:
        u = a.get("url", "").strip().lower()
        t = a.get("title", "").strip().lower()
        if not t or not u:
            continue
        # Normalize title for dedup
        t_norm = "".join(c for c in t if c.isalnum() or c == " ")[:80]
        if u in seen_urls or t_norm in seen_titles:
            continue
        seen_urls.add(u)
        seen_titles.add(t_norm)
        out.append(a)
    return out


# ── Gemini summarize + categorize ───────────────

def gemini_call(prompt, model="gemini-2.5-flash", max_retries=2):
    if not GEMINI_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 16000}
    }
    for attempt in range(max_retries):
        try:
            resp = http_post(url, body, timeout=90)
            data = json.loads(resp)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"  [gemini retry {attempt+1}] {e}")
            time.sleep(2)
    return None


def gemini_categorize_and_translate(articles):
    """Gemini takes raw articles → returns categorized + summarized digest."""
    if not articles:
        return None
    art_text = "\n\n".join([
        f"#{i+1} [{a['_origin']}] {a['title']}\nSource: {a['source']}\nURL: {a['url']}\nSnippet: {a.get('snippet','')[:300]}"
        for i, a in enumerate(articles[:60])
    ])

    prompt = f"""Bạn là biên tập viên tin tức AI cho cộng đồng Việt Nam (đối tượng: producer, creative, manager, người quan tâm AI).

Đọc list bài viết AI dưới đây và tạo bản tin daily digest theo format JSON. Tiếng Việt tự nhiên, súc tích, có insight.

QUY TẮC QUAN TRỌNG:
- MỌI tin đều phải có field "why" giải thích ý nghĩa/tác động — không tin nào chỉ có headline trống.
- "why" = 1-2 dòng tiếng Việt giải thích vì sao tin này đáng quan tâm với người đọc (production/creative/manager). Cụ thể, không sáo rỗng. Ví dụ tốt: "Có nghĩa team production có thể gen 4K trực tiếp, không cần upscale post — tiết kiệm 30% post time." Ví dụ xấu: "Đây là bước tiến lớn cho AI."

Yêu cầu nội dung:
1. Chọn 1 TOP STORY quan trọng nhất hôm nay (impact lớn nhất với ngành, hoặc tin breaking)
2. Chọn 5-8 QUICK HITS — tin đáng đọc, mỗi tin headline punchy + why ngắn
3. Chọn 2-4 PRODUCTION AI — tin về AI image/video/production tools (Higgsfield, Kling, Seedance, Veo, Sora, Runway, Midjourney, FLUX...)
4. Chọn 0-3 VIETNAM — tin AI Việt Nam nếu có (ưu tiên tin từ vnexpress, genk, hoặc các tin về VinAI, FPT, Zalo, Viettel)
5. Chọn 2-4 RESEARCH — papers/models nổi bật từ HuggingFace / arXiv (nếu có trong list, dùng "huggingface" hoặc "arxiv" trong _origin)
6. Chọn 2-4 OPEN SOURCE — repos GitHub trending AI (nếu có _origin "github")
7. Loại tin trùng lặp, clickbait, low quality

Output CHÍNH XÁC theo schema JSON sau (không thêm text ngoài JSON):

{{
  "top_story": {{
    "headline": "Tiêu đề tiếng Việt 8-12 từ",
    "summary": "2-3 câu giải thích tin",
    "why": "1-2 dòng cụ thể: TẠI SAO QUAN TRỌNG cho người đọc VN (production/creative/manager) — implication thực tế, không sáo rỗng",
    "source": "Tên nguồn",
    "url": "URL gốc",
    "tags": ["tag1", "tag2"]
  }},
  "quick_hits": [
    {{"headline": "1 câu súc tích tiếng Việt", "why": "1 dòng giải thích ý nghĩa/tác động", "source": "...", "url": "...", "tags": ["..."]}},
    ...
  ],
  "production": [
    {{"headline": "...", "summary": "1 dòng context", "why": "1-2 dòng implication cho production team", "source": "...", "url": "...", "tags": ["..."]}}
  ],
  "vietnam": [
    {{"headline": "...", "why": "1 dòng ý nghĩa với thị trường VN", "source": "...", "url": "..."}}
  ],
  "research": [
    {{"headline": "Tên paper/model bằng tiếng Việt", "summary": "1-2 dòng giải thích bằng ngôn ngữ đời thường (không jargon)", "why": "1 dòng implication thực tế cho production/creative", "source": "HuggingFace Papers OR arXiv", "url": "...", "tags": ["..."]}}
  ],
  "opensource": [
    {{"headline": "Tên repo + 1 dòng mô tả", "why": "1 dòng tại sao đáng quan tâm", "source": "GitHub Trending", "url": "...", "stars": "số sao nếu có"}}
  ]
}}

Articles:
{art_text}

Trả về JSON only, không markdown wrapper."""

    raw = gemini_call(prompt)
    if not raw:
        return None
    # Clean markdown wrapper if Gemini added it
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [err] Gemini JSON parse: {e}")
        print(f"  [raw first 500]: {raw[:500]}")
        return None


# ── Claude weekly insight ──────────────────────

def claude_call(prompt, model="claude-sonnet-4-5-20250929"):
    if not ANTHROPIC_KEY:
        return None
    body = {
        "model": model,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        resp = http_post(
            "https://api.anthropic.com/v1/messages",
            body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01"
            },
            timeout=120
        )
        data = json.loads(resp)
        return data["content"][0]["text"]
    except Exception as e:
        print(f"  [err] claude: {e}")
        return None


def claude_weekly_insight(week_digest_summary):
    """Claude writes the weekly insight piece (run only on Sunday)."""
    prompt = f"""Bạn là AI Mentor — biên tập viên cấp cao theo dõi cộng đồng AI cho người làm production/sáng tạo Việt Nam.

Đọc bản tóm tắt tuần dưới đây và viết 1 đoạn INSIGHT TUẦN (2-3 paragraphs, ~150-250 từ tiếng Việt) phân tích:
- Pattern/trend lớn nhất tuần này
- Implication cho người làm sáng tạo VN (production house, agency, creator)
- Leverage point cụ thể nên hành động

Tone: thẳng thắn, không sáo rỗng, có chiều sâu. Như AI Mentor đang nói chuyện riêng với 1 EP có kinh nghiệm. Không chế tạo số liệu.

Tóm tắt tuần:
{week_digest_summary}

Output: chỉ insight tuần, không cần header."""
    return claude_call(prompt)


# ── Main pipeline ──────────────────────────────

def main():
    print(f"=== AI News Fetch — {DATE_STR} ===\n")

    # 1. Fetch all sources
    all_articles = []

    print("Fetching Brave...")
    for tag, query, freshness in BRAVE_QUERIES:
        articles = fetch_brave(query, freshness=freshness, count=8)
        for a in articles:
            a["_query_tag"] = tag
        all_articles.extend(articles)
        print(f"  {tag}: {len(articles)}")
        time.sleep(0.5)  # rate limit

    print("\nFetching Reddit...")
    for sub in REDDIT_SUBS:
        articles = fetch_reddit(sub, limit=12)
        all_articles.extend(articles)
        print(f"  r/{sub}: {len(articles)}")
        time.sleep(1)

    print("\nFetching HackerNews...")
    hn = fetch_hackernews(limit=15)
    all_articles.extend(hn)
    print(f"  HN: {len(hn)}")

    print("\nFetching Tier-1 RSS feeds...")
    for name, url in RSS_FEEDS:
        articles = fetch_rss(name, url, limit=8, ai_filter=False)
        all_articles.extend(articles)
        print(f"  {name}: {len(articles)}")
        time.sleep(0.5)

    print("\nFetching Vietnam RSS...")
    for name, url in VN_RSS:
        articles = fetch_rss(name, url, limit=10, ai_filter=True)  # filter VN feeds for AI keyword
        all_articles.extend(articles)
        print(f"  {name}: {len(articles)} (AI-filtered)")
        time.sleep(0.5)

    print("\nFetching HuggingFace papers...")
    hf = fetch_huggingface_papers(limit=8)
    all_articles.extend(hf)
    print(f"  HF papers: {len(hf)}")

    print("\nFetching GitHub trending AI...")
    gh = fetch_github_trending_ai(limit=10)
    all_articles.extend(gh)
    print(f"  GitHub: {len(gh)}")

    print(f"\nTotal raw: {len(all_articles)}")
    all_articles = dedupe(all_articles)
    print(f"After dedupe: {len(all_articles)}")

    # 2. Sort: prefer recent + score
    def sort_key(a):
        score = a.get("score", 0)
        if a["_origin"] == "brave":
            score = 50  # default for brave (no score)
        return -score
    all_articles.sort(key=sort_key)

    # 3. Gemini categorize
    print("\nGemini categorizing...")
    digest = gemini_categorize_and_translate(all_articles)
    if not digest:
        print("[FATAL] Gemini failed, abort")
        sys.exit(1)

    # 4. Claude weekly insight (only Sundays)
    insight = None
    if IS_SUNDAY and ANTHROPIC_KEY:
        print("\nSunday — Claude weekly insight...")
        summary_for_claude = json.dumps(digest, ensure_ascii=False, indent=2)[:6000]
        insight = claude_weekly_insight(summary_for_claude)

    # 5. Build final output
    output = {
        "date": DATE_STR,
        "updated_at": NOW.isoformat(),
        "weekday": NOW.strftime("%A"),
        "top_story": digest.get("top_story"),
        "quick_hits": digest.get("quick_hits", []),
        "production": digest.get("production", []),
        "vietnam": digest.get("vietnam", []),
        "research": digest.get("research", []),
        "opensource": digest.get("opensource", []),
        "insight": insight,
        "sources_count": {
            "raw": len(all_articles),
            "brave": sum(1 for a in all_articles if a["_origin"] == "brave"),
            "reddit": sum(1 for a in all_articles if a["_origin"] == "reddit"),
            "hackernews": sum(1 for a in all_articles if a["_origin"] == "hackernews"),
            "rss": sum(1 for a in all_articles if a["_origin"] == "rss"),
            "huggingface": sum(1 for a in all_articles if a["_origin"] == "huggingface"),
            "github": sum(1 for a in all_articles if a["_origin"] == "github"),
        }
    }

    # 6. Write files
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    year_dir = NEWS_DIR / NOW.strftime("%Y") / NOW.strftime("%m")
    year_dir.mkdir(parents=True, exist_ok=True)

    daily_file = year_dir / f"{NOW.strftime('%d')}.json"
    latest_file = NEWS_DIR / "latest.json"

    daily_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # 7. Update archive index
    archive_index_file = NEWS_DIR / "archive-index.json"
    archive_index = {"dates": []}
    if archive_index_file.exists():
        try:
            archive_index = json.loads(archive_index_file.read_text())
        except Exception:
            pass
    if DATE_STR not in archive_index["dates"]:
        archive_index["dates"].append(DATE_STR)
        archive_index["dates"].sort(reverse=True)
    archive_index_file.write_text(json.dumps(archive_index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✓ Wrote {daily_file}")
    print(f"✓ Wrote {latest_file}")
    print(f"✓ Archive: {len(archive_index['dates'])} dates")
    print(f"\nTop: {output['top_story']['headline'] if output['top_story'] else 'N/A'}")
    print(f"Quick hits: {len(output['quick_hits'])}")
    print(f"Production: {len(output['production'])}")
    print(f"Vietnam: {len(output['vietnam'])}")
    print(f"Insight: {'YES' if insight else 'NO (not Sunday or no Anthropic key)'}")


if __name__ == "__main__":
    main()
