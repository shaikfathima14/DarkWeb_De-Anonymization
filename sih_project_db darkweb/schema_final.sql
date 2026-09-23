-- ============================================================
-- SIH26151 - Dark Web Threat Actor De-anonymization
-- PostgreSQL Schema (Person 5 - Database + Graph Engineer)
-- FINAL VERSION - includes reply_to_post_id and listing_id as TEXT
-- ============================================================

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'analyst',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE datasets (
    dataset_id SERIAL PRIMARY KEY,
    uploaded_by INTEGER REFERENCES users(user_id),
    file_name TEXT NOT NULL,
    dataset_type TEXT,
    status TEXT DEFAULT 'uploaded',
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE actors (
    actor_id INTEGER PRIMARY KEY,
    username TEXT,
    post_count INTEGER,
    total_words INTEGER,
    avg_word_count FLOAT,
    avg_sentence_length FLOAT,
    avg_punctuation FLOAT,
    avg_uppercase_ratio FLOAT,
    avg_digit_count FLOAT,
    forums_used INTEGER,
    topics_used INTEGER,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    data_quality_flag TEXT,
    dataset_id INTEGER REFERENCES datasets(dataset_id)
);

CREATE TABLE dataset_records (
    post_id INTEGER PRIMARY KEY,
    actor_id INTEGER REFERENCES actors(actor_id),
    post_text TEXT,
    "timestamp" TIMESTAMP,
    forum_id INTEGER,
    forum_name TEXT,
    topic_id INTEGER,
    topic_title TEXT,
    category TEXT,
    source TEXT,
    thread_id INTEGER,
    reply_to_post_id TEXT,          -- TEXT: some values are "ROOT_..." markers
    reply_to_post_id_status TEXT,
    listing_id TEXT,                -- TEXT: some values are "/listing/123" style
    listing_title TEXT,
    language TEXT,
    word_count INTEGER,
    avg_sentence_length FLOAT,
    punctuation_count INTEGER,
    posting_hour INTEGER,
    dataset_id INTEGER REFERENCES datasets(dataset_id)
);

CREATE TABLE entities (
    entity_id SERIAL PRIMARY KEY,
    actor_id INTEGER REFERENCES actors(actor_id),
    entity_type TEXT NOT NULL,
    value TEXT NOT NULL,
    source_dataset_id INTEGER REFERENCES datasets(dataset_id),
    UNIQUE (entity_type, value, actor_id)
);

CREATE TABLE actor_features (
    feature_id SERIAL PRIMARY KEY,
    actor_id INTEGER REFERENCES actors(actor_id),
    feature_name TEXT NOT NULL,
    feature_value FLOAT,
    computed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE investigations (
    investigation_id SERIAL PRIMARY KEY,
    created_by INTEGER REFERENCES users(user_id),
    title TEXT,
    status TEXT DEFAULT 'open',
    transcript JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE correlations (
    correlation_id SERIAL PRIMARY KEY,
    investigation_id INTEGER REFERENCES investigations(investigation_id),
    actor_a_id INTEGER REFERENCES actors(actor_id),
    actor_b_id INTEGER REFERENCES actors(actor_id),
    confidence FLOAT,
    risk_level TEXT,
    evidence JSONB,
    excluded_evidence TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    investigation_id INTEGER REFERENCES investigations(investigation_id),
    file_path TEXT,
    generated_by INTEGER REFERENCES users(user_id),
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_entities_actor_id ON entities(actor_id);
CREATE INDEX idx_entities_type_value ON entities(entity_type, value);
CREATE INDEX idx_dataset_records_actor_id ON dataset_records(actor_id);
CREATE INDEX idx_dataset_records_forum_id ON dataset_records(forum_id);
CREATE INDEX idx_correlations_actors ON correlations(actor_a_id, actor_b_id);
CREATE INDEX idx_actor_features_actor_id ON actor_features(actor_id);
