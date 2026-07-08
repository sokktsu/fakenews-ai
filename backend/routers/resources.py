"""Resources Router"""
from fastapi import APIRouter
router = APIRouter()

RESOURCES = [
    {
        "id": 1,
        "title": "How to Spot Fake News",
        "description": "A comprehensive guide from IFLA on identifying misinformation online.",
        "url": "https://www.ifla.org/publications/node/11174",
        "category": "fact-checking",
        "source": "IFLA",
    },
    {
        "id": 2,
        "title": "NewsGuard — News Reliability Ratings",
        "description": "Browser extension that rates news websites for reliability.",
        "url": "https://www.newsguardtech.com/",
        "category": "tool",
        "source": "NewsGuard",
    },
    {
        "id": 3,
        "title": "Snopes Fact-Checking",
        "description": "One of the oldest and most trusted fact-checking websites.",
        "url": "https://www.snopes.com/",
        "category": "fact-checking",
        "source": "Snopes",
    },
    {
        "id": 4,
        "title": "PolitiFact",
        "description": "Fact-checking journalism for political claims and news.",
        "url": "https://www.politifact.com/",
        "category": "fact-checking",
        "source": "PolitiFact",
    },
    {
        "id": 5,
        "title": "Media Literacy Now",
        "description": "Advocating for media literacy education across the United States.",
        "url": "https://medialiteracynow.org/",
        "category": "education",
        "source": "Media Literacy Now",
    },
    {
        "id": 6,
        "title": "AI Ethics Guidelines — UNESCO",
        "description": "UNESCO Recommendation on the Ethics of Artificial Intelligence.",
        "url": "https://unesdoc.unesco.org/ark:/48223/pf0000381137",
        "category": "ai-ethics",
        "source": "UNESCO",
    },
    {
        "id": 7,
        "title": "First Draft — Fighting Misinformation",
        "description": "Guides and tools for journalists combating misinformation.",
        "url": "https://firstdraftnews.org/",
        "category": "journalism",
        "source": "First Draft",
    },
    {
        "id": 8,
        "title": "MIT Media Lab — Fake News Study",
        "description": "Groundbreaking research on how fake news spreads on social media.",
        "url": "https://www.media.mit.edu/",
        "category": "research",
        "source": "MIT Media Lab",
    },
]


@router.get("/")
async def list_resources(category: str = None):
    if category:
        return [r for r in RESOURCES if r["category"] == category]
    return RESOURCES


@router.get("/categories")
async def get_categories():
    cats = list({r["category"] for r in RESOURCES})
    return cats
