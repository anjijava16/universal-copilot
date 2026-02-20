"""
core/tools/web_tools.py — Web Tool Executors
=============================================
web_fetch  → fetch and clean text content from a URL
web_search → search the web via Brave Search API
"""

import json
import httpx
from bs4 import BeautifulSoup
import structlog

from core.config import settings

log = structlog.get_logger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; UniversalCopilot/1.0)"
}


# ─── web_fetch ────────────────────────────────────────────────────────────────

async def execute_web_fetch(args: dict) -> str:
    url           = args.get("url", "")
    extract_links = bool(args.get("extract_links", False))
    max_chars     = 8000

    if not url:
        return json.dumps({"error": "No URL provided."})

    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must start with http:// or https://"})

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, headers=HEADERS
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        # Plain text / markdown / JSON — return as-is
        if any(ct in content_type for ct in ("text/plain", "application/json", "text/markdown")):
            text = response.text[:max_chars]
            return json.dumps({
                "url":         url,
                "status_code": response.status_code,
                "content":     text,
                "truncated":   len(response.text) > max_chars,
            })

        # HTML — parse and extract clean text
        soup = BeautifulSoup(response.text, "lxml")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "iframe", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Deduplicate blank lines
        lines = [l for l in text.splitlines() if l.strip()]
        clean = "\n".join(lines)[:max_chars]

        result: dict = {
            "url":         url,
            "status_code": response.status_code,
            "content":     clean,
            "truncated":   len(text) > max_chars,
        }

        if extract_links:
            links = []
            for a in soup.find_all("a", href=True)[:30]:
                href = a["href"]
                if href.startswith("http"):
                    links.append({"text": a.get_text(strip=True), "href": href})
            result["links"] = links

        return json.dumps(result)

    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}: {url}"})
    except httpx.TimeoutException:
        return json.dumps({"error": f"Request timed out: {url}"})
    except Exception as e:
        log.error("web_fetch.error", url=url, error=str(e))
        return json.dumps({"error": str(e)})


# ─── web_search ───────────────────────────────────────────────────────────────

async def execute_web_search(args: dict) -> str:
    query = args.get("query", "")
    top_k = min(int(args.get("top_k", 5)), 10)

    if not query:
        return json.dumps({"error": "No query provided."})

    # Brave Search API
    if settings.BRAVE_SEARCH_API_KEY:
        return await _brave_search(query, top_k)

    # Fallback: DuckDuckGo instant answers (no API key needed)
    return await _duckduckgo_search(query, top_k)


async def _brave_search(query: str, top_k: int) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": top_k},
                headers={
                    "Accept":               "application/json",
                    "Accept-Encoding":      "gzip",
                    "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("web", {}).get("results", [])[:top_k]:
            results.append({
                "title":   item.get("title"),
                "url":     item.get("url"),
                "snippet": item.get("description"),
            })

        return json.dumps({"query": query, "results": results, "source": "brave"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def _duckduckgo_search(query: str, top_k: int) -> str:
    """Fallback: DuckDuckGo HTML scrape (no API key needed)."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=HEADERS,
            )
        soup = BeautifulSoup(response.text, "lxml")
        results = []
        for result in soup.select(".result")[:top_k]:
            title_el  = result.select_one(".result__title")
            url_el    = result.select_one(".result__url")
            snip_el   = result.select_one(".result__snippet")
            if title_el:
                results.append({
                    "title":   title_el.get_text(strip=True),
                    "url":     url_el.get_text(strip=True) if url_el else "",
                    "snippet": snip_el.get_text(strip=True) if snip_el else "",
                })
        return json.dumps({"query": query, "results": results, "source": "duckduckgo"})
    except Exception as e:
        return json.dumps({"error": str(e)})
