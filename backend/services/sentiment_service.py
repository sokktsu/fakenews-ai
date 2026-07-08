"""
Sentiment Analysis Service
"""
from loguru import logger


def analyze_sentiment(text: str) -> dict:
    """Returns sentiment label and score."""
    try:
        from textblob import TextBlob
        blob  = TextBlob(text)
        pol   = blob.sentiment.polarity  # -1 to 1
        if pol > 0.1:
            label = "POSITIVE"
        elif pol < -0.1:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
        return {"label": label, "score": round(pol, 4)}
    except Exception as e:
        logger.warning(f"Sentiment analysis failed: {e}")
        return {"label": "NEUTRAL", "score": 0.0}
