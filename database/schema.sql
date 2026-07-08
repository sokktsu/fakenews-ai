-- ============================================================
-- FAKE NEWS AI — PostgreSQL Schema
-- Run: psql -U postgres -d fakenews_db -f schema.sql
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin        BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);

-- Analyzed Articles
CREATE TABLE IF NOT EXISTS analyzed_articles (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    input_type      VARCHAR(20) NOT NULL,     -- text | url | image
    raw_text        TEXT,
    source_url      VARCHAR(500),
    title           VARCHAR(500),
    label           VARCHAR(10) NOT NULL,     -- REAL | FAKE
    confidence      FLOAT NOT NULL,
    bert_score      FLOAT,
    roberta_score   FLOAT,
    bert_multilingual_score FLOAT,
    lstm_score      FLOAT,
    logistic_score  FLOAT,
    ensemble_score  FLOAT,
    sentiment       VARCHAR(20),
    sentiment_score FLOAT,
    keywords        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Migration: add score columns for RoBERTa & multilingual BERT on pre-existing tables
-- (safe to run repeatedly; CREATE TABLE above already includes them for fresh installs)
ALTER TABLE analyzed_articles ADD COLUMN IF NOT EXISTS roberta_score FLOAT;
ALTER TABLE analyzed_articles ADD COLUMN IF NOT EXISTS bert_multilingual_score FLOAT;

-- Uploaded Images
CREATE TABLE IF NOT EXISTS uploaded_images (
    id              SERIAL PRIMARY KEY,
    filename        VARCHAR(255),
    file_path       VARCHAR(500),
    extracted_text  TEXT,
    article_id      INTEGER REFERENCES analyzed_articles(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Explanations
CREATE TABLE IF NOT EXISTS explanations (
    id                      SERIAL PRIMARY KEY,
    article_id              INTEGER REFERENCES analyzed_articles(id) ON DELETE CASCADE,
    suspicious_words        JSONB,
    emotional_words         JSONB,
    misleading_phrases      JSONB,
    credibility_indicators  JSONB,
    highlighted_sentences   JSONB,
    shap_values             JSONB,
    attention_weights       JSONB,
    full_explanation        TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id              SERIAL PRIMARY KEY,
    article_id      INTEGER REFERENCES analyzed_articles(id) ON DELETE CASCADE,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    was_accurate    BOOLEAN NOT NULL,
    correct_label   VARCHAR(10),
    comment         TEXT,
    reviewed        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Retraining Data
CREATE TABLE IF NOT EXISTS retraining_data (
    id          SERIAL PRIMARY KEY,
    text        TEXT NOT NULL,
    label       VARCHAR(10) NOT NULL,
    source      VARCHAR(50),   -- feedback | admin | dataset
    verified    BOOLEAN DEFAULT FALSE,
    used        BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Community Posts
CREATE TABLE IF NOT EXISTS community_posts (
    id          SERIAL PRIMARY KEY,
    author_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title       VARCHAR(300) NOT NULL,
    content     TEXT NOT NULL,
    category    VARCHAR(50) DEFAULT 'discussion',
    source_url  VARCHAR(500),
    likes       INTEGER DEFAULT 0,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Comments
CREATE TABLE IF NOT EXISTS comments (
    id          SERIAL PRIMARY KEY,
    post_id     INTEGER REFERENCES community_posts(id) ON DELETE CASCADE,
    author_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    author_name VARCHAR(100),
    content     TEXT NOT NULL,
    likes       INTEGER DEFAULT 0,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_articles_label      ON analyzed_articles(label);
CREATE INDEX IF NOT EXISTS idx_articles_created    ON analyzed_articles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_article    ON feedback(article_id);
CREATE INDEX IF NOT EXISTS idx_community_category  ON community_posts(category);
CREATE INDEX IF NOT EXISTS idx_retraining_verified ON retraining_data(verified);
