import asyncio
import re
import urllib.parse
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import httpx
import feedparser
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OpinionPulseApp/2.5"
}

def clean_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", cleaned).strip()

def normalize_date(dt_obj: Optional[datetime]) -> str:
    if not dt_obj:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return dt_obj.strftime("%Y-%m-%d")

async def fetch_reddit_mentions(topic: str, time_range: str = "all", limit: int = 35) -> List[Dict[str, Any]]:
    """Recolecta discusiones y comentarios de debate en Reddit vía RSS de /r/all."""
    mentions = []
    encoded_topic = urllib.parse.quote(topic)
    
    time_map = {
        "24h": "day",
        "7d": "week",
        "30d": "month",
        "1y": "year",
        "all": "all"
    }
    reddit_t = time_map.get(time_range, "all")
    
    urls = [
        f"https://www.reddit.com/r/all/search.rss?q={encoded_topic}&sort=relevance&t={reddit_t}&limit=25",
        f"https://www.reddit.com/r/all/search.rss?q={encoded_topic}&sort=comments&t={reddit_t}&limit=25"
    ]
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        title = clean_html(entry.get("title", ""))
                        summary = clean_html(entry.get("summary", ""))
                        link = entry.get("link", "")
                        author = clean_html(entry.get("author", "redditor"))
                        
                        if any(m["title"] == title for m in mentions):
                            continue
                            
                        iso_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                        ts = time.time()
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                            iso_date = dt.strftime("%Y-%m-%d")
                            ts = dt.timestamp()
                            
                        content = f"{title}. {summary}".strip()
                        if len(content) > 500:
                            content = content[:500] + "..."
                            
                        mentions.append({
                            "id": f"reddit_{len(mentions)+1}",
                            "platform": "Reddit",
                            "source_name": "Reddit Community",
                            "title": title,
                            "content": content,
                            "author": author if author else "u/comunidad",
                            "url": link,
                            "engagement": "Debate Comunitario",
                            "score": 15,
                            "published_at": iso_date,
                            "iso_date": iso_date,
                            "timestamp": ts,
                            "raw_text": f"[Reddit] {title}: {summary}"
                        })
                        if len(mentions) >= limit:
                            break
            except Exception as e:
                print(f"[Reddit Harvester Error] {e}")
                
            if len(mentions) >= limit:
                break
                
    return mentions

async def fetch_news_mentions(topic: str, time_range: str = "all", limit: int = 40) -> List[Dict[str, Any]]:
    """Recolecta noticias, crónicas y columnas de opinión vía Google News RSS."""
    mentions = []
    
    time_queries = {
        "24h": f"{topic} when:1d",
        "7d": f"{topic} when:7d",
        "30d": f"{topic} when:30d",
        "1y": f"{topic} when:1y",
        "all": topic
    }
    q = time_queries.get(time_range, topic)
    encoded_topic = urllib.parse.quote(q)
    encoded_opinion = urllib.parse.quote(f"{q} (opinion OR debate OR critica OR analisis OR dimision OR gobierno OR polemica)")
    
    feed_urls = [
        f"https://news.google.com/rss/search?q={encoded_topic}&hl=es-419&gl=ES&ceid=ES:es",
        f"https://news.google.com/rss/search?q={encoded_opinion}&hl=es-419&gl=ES&ceid=ES:es",
        f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"
    ]
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
        for feed_url in feed_urls:
            try:
                resp = await client.get(feed_url)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        title = clean_html(entry.get("title", ""))
                        summary = clean_html(entry.get("summary", ""))
                        link = entry.get("link", "")
                        published = entry.get("published", "")
                        source = entry.get("source", {}).get("title", "Medio de Comunicación")
                        
                        if any(m["title"] == title for m in mentions):
                            continue
                            
                        iso_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                        ts = time.time()
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                            iso_date = dt.strftime("%Y-%m-%d")
                            ts = dt.timestamp()
                            
                        content = f"{title}. {summary}".strip()
                        if len(content) > 500:
                            content = content[:500] + "..."
                            
                        mentions.append({
                            "id": f"news_{len(mentions)+1}",
                            "platform": "Medios / Noticias",
                            "source_name": source,
                            "title": title,
                            "content": content,
                            "author": source,
                            "url": link,
                            "engagement": "Prensa Digital / Editorial",
                            "score": 10,
                            "published_at": published[:16] if published else iso_date,
                            "iso_date": iso_date,
                            "timestamp": ts,
                            "raw_text": f"[{source}] {title}: {summary}"
                        })
                        if len(mentions) >= limit:
                            break
            except Exception as e:
                print(f"[News Harvester Error] {e}")
                
            if len(mentions) >= limit:
                break
                
    return mentions

async def fetch_social_web_mentions(topic: str, time_range: str = "all", limit: int = 30) -> List[Dict[str, Any]]:
    """Recolecta opiniones ciudadanas y debates en redes y foros."""
    mentions = []
    queries = [
        f"{topic} (debate OR polemica OR apoyo OR critica OR postura OR redes)",
        f"{topic} (declaraciones OR acusaciones OR defensa OR reaccion)",
        f"{topic} opinion viral"
    ]
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
        for q in queries:
            feed_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=es-419&gl=ES&ceid=ES:es"
            try:
                resp = await client.get(feed_url)
                if resp.status_code == 200:
                    feed = feedparser.parse(resp.text)
                    for entry in feed.entries:
                        title = clean_html(entry.get("title", ""))
                        summary = clean_html(entry.get("summary", ""))
                        link = entry.get("link", "")
                        source = entry.get("source", {}).get("title", "Foro / Red Social")
                        
                        if any(m["title"] == title for m in mentions):
                            continue
                            
                        iso_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                        ts = time.time()
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                            iso_date = dt.strftime("%Y-%m-%d")
                            ts = dt.timestamp()
                            
                        content = f"{title}. {summary}".strip()
                        if len(content) > 500:
                            content = content[:500] + "..."
                            
                        mentions.append({
                            "id": f"social_{len(mentions)+1}",
                            "platform": "X / Twitter & Redes",
                            "source_name": f"Debate Público ({source})",
                            "title": title,
                            "content": content,
                            "author": source,
                            "url": link,
                            "engagement": "Conversación y Redes",
                            "score": 8,
                            "published_at": iso_date,
                            "iso_date": iso_date,
                            "timestamp": ts,
                            "raw_text": f"[Redes / {source}] {title}: {summary}"
                        })
                        if len(mentions) >= limit:
                            break
            except Exception as e:
                print(f"[Social Harvester Error] {e}")
                
            if len(mentions) >= limit:
                break
                
    return mentions

async def harvest_all_mentions(
    topic: str,
    sources: Optional[List[str]] = None,
    time_range: str = "all",
    mcp_settings: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Orquesta la recolección multicanal con filtrado temporal."""
    if sources is None:
        sources = ["reddit", "news", "social_web"]
    if mcp_settings is None:
        mcp_settings = {}
        
    tasks = []
    if "reddit" in sources:
        tasks.append(fetch_reddit_mentions(topic, time_range=time_range, limit=35))
    if "news" in sources:
        tasks.append(fetch_news_mentions(topic, time_range=time_range, limit=40))
    if "social_web" in sources or "x" in sources or "facebook" in sources:
        tasks.append(fetch_social_web_mentions(topic, time_range=time_range, limit=30))
        
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_mentions: List[Dict[str, Any]] = []
    
    for res in results:
        if isinstance(res, list):
            all_mentions.extend(res)
            
    all_mentions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return all_mentions
