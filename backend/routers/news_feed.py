"""
News Feed Router — Uses free NewsAPI / GNews / MediaStack
"""
from fastapi import APIRouter, HTTPException
import httpx, os
from loguru import logger

router = APIRouter()

NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")


async def _fetch_newsapi(query: str = "misinformation") -> list:
    if not NEWS_API_KEY:
        return []
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=10&apiKey={NEWS_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
            return data.get("articles", [])[:10]
    except Exception as e:
        logger.warning(f"NewsAPI error: {e}")
        return []


async def _fetch_gnews(query: str = "fake news") -> list:
    if not GNEWS_API_KEY:
        return []
    url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=10&apikey={GNEWS_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            data = resp.json()
            articles = data.get("articles", [])
            # Normalize to NewsAPI format
            return [
                {
                    "title":       a.get("title"),
                    "description": a.get("description"),
                    "url":         a.get("url"),
                    "source":      {"name": a.get("source", {}).get("name")},
                    "publishedAt": a.get("publishedAt"),
                    "urlToImage":  a.get("image"),
                }
                for a in articles
            ]
    except Exception as e:
        logger.warning(f"GNews error: {e}")
        return []


# Fallback static headlines for demo when no API key
DEMO_HEADLINES = [
    {"title": "Researchers Develop AI System That Detects Deepfakes With 96% Accuracy",
     "description": "A new deep learning model can identify manipulated videos in real time.",
     "source": {"name": "Tech News Demo"}, "url": "#", "publishedAt": "2024-01-15"},
    {"title": "Social Media Platforms Pledge to Label AI-Generated Content",
     "description": "Major platforms announce new policies to combat the spread of synthetic media.",
     "source": {"name": "Media Watch Demo"}, "url": "#", "publishedAt": "2024-01-14"},
    {"title": "Study: 62% of Shared News Articles Not Read Before Sharing",
     "description": "New research highlights how misinformation spreads through social networks.",
     "source": {"name": "Research Demo"}, "url": "#", "publishedAt": "2024-01-13"},
    {"title": "UNESCO Launches Global Media Literacy Campaign for 2024",
     "description": "International effort to improve critical thinking about online information.",
     "source": {"name": "UNESCO Demo"}, "url": "#", "publishedAt": "2024-01-12"},
    {"title": "Philippine Fact-Checkers Network Expands Verification Services",
     "description": "Local journalists collaborate to address regional misinformation challenges.",
     "source": {"name": "PH Media Demo"}, "url": "#", "publishedAt": "2024-01-11"},
]


@router.get("/")
async def get_news_feed(query: str = "misinformation fake news"):
    articles = await _fetch_newsapi(query)
    if not articles:
        articles = await _fetch_gnews(query)
    if not articles:
        articles = DEMO_HEADLINES
    return {"articles": articles, "total": len(articles)}
