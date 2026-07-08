"""
SQLAlchemy ORM Models
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database.connection import Base


class PredictionLabel(str, enum.Enum):
    REAL = "REAL"
    FAKE = "FAKE"


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    username      = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin      = Column(Boolean, default=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    articles      = relationship("AnalyzedArticle", back_populates="user")
    feedbacks     = relationship("Feedback", back_populates="user")
    posts         = relationship("CommunityPost", back_populates="author")


class AnalyzedArticle(Base):
    __tablename__ = "analyzed_articles"
    id                      = Column(Integer, primary_key=True, index=True)
    user_id                 = Column(Integer, ForeignKey("users.id"), nullable=True)
    input_type              = Column(String(20))   # text | url | image
    raw_text                = Column(Text)
    source_url              = Column(String(500), nullable=True)
    title                   = Column(String(500), nullable=True)
    label                   = Column(Enum(PredictionLabel))
    confidence              = Column(Float)
    bert_score              = Column(Float)
    roberta_score           = Column(Float, nullable=True)
    bert_multilingual_score = Column(Float, nullable=True)
    lstm_score              = Column(Float)
    logistic_score          = Column(Float)
    ensemble_score          = Column(Float)
    sentiment               = Column(String(20))
    sentiment_score         = Column(Float)
    keywords                = Column(JSON)
    created_at              = Column(DateTime(timezone=True), server_default=func.now())

    user        = relationship("User", back_populates="articles")
    explanation = relationship("Explanation", back_populates="article", uselist=False)
    feedback    = relationship("Feedback", back_populates="article")


class UploadedImage(Base):
    __tablename__ = "uploaded_images"
    id             = Column(Integer, primary_key=True, index=True)
    filename       = Column(String(255))
    file_path      = Column(String(500))
    extracted_text = Column(Text)
    article_id     = Column(Integer, ForeignKey("analyzed_articles.id"), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())


class Explanation(Base):
    __tablename__ = "explanations"
    id                     = Column(Integer, primary_key=True, index=True)
    article_id             = Column(Integer, ForeignKey("analyzed_articles.id"))
    suspicious_words       = Column(JSON)
    emotional_words        = Column(JSON)
    misleading_phrases     = Column(JSON)
    credibility_indicators = Column(JSON)
    highlighted_sentences  = Column(JSON)
    shap_values            = Column(JSON, nullable=True)
    attention_weights      = Column(JSON, nullable=True)
    full_explanation       = Column(Text)
    created_at             = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("AnalyzedArticle", back_populates="explanation")


class Feedback(Base):
    __tablename__ = "feedback"
    id            = Column(Integer, primary_key=True, index=True)
    article_id    = Column(Integer, ForeignKey("analyzed_articles.id"))
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    was_accurate  = Column(Boolean)
    correct_label = Column(Enum(PredictionLabel), nullable=True)
    comment       = Column(Text, nullable=True)
    reviewed      = Column(Boolean, default=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("AnalyzedArticle", back_populates="feedback")
    user    = relationship("User", back_populates="feedbacks")


class RetrainingData(Base):
    __tablename__ = "retraining_data"
    id         = Column(Integer, primary_key=True, index=True)
    text       = Column(Text, nullable=False)
    label      = Column(Enum(PredictionLabel), nullable=False)
    source     = Column(String(50))
    verified   = Column(Boolean, default=False)
    used       = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommunityPost(Base):
    __tablename__ = "community_posts"
    id          = Column(Integer, primary_key=True, index=True)
    author_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    title       = Column(String(300), nullable=False)
    content     = Column(Text, nullable=False)
    category    = Column(String(50))
    source_url  = Column(String(500), nullable=True)
    likes       = Column(Integer, default=0)
    is_approved = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    author   = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Comment(Base):
    __tablename__ = "comments"
    id          = Column(Integer, primary_key=True, index=True)
    post_id     = Column(Integer, ForeignKey("community_posts.id"))
    author_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    author_name = Column(String(100))
    content     = Column(Text, nullable=False)
    likes       = Column(Integer, default=0)
    is_approved = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("CommunityPost", back_populates="comments")
