"""
SIH26151 - Load cleaned datasets into PostgreSQL
Run this AFTER schema.sql has been executed on your database.

Before running:
1. pip install psycopg2-binary pandas
2. Put this script in the SAME FOLDER as:
   - SIH26151_darkweb_master_dataset_CLEANED.csv
   - correlation_feature_matrix.csv
   - persona_profiles_CLEANED.json
3. Update the DB_CONFIG below with your actual password.
"""

import psycopg2
import pandas as pd
import json
import os
from dotenv import load_dotenv

# ---------- 1. DATABASE CONNECTION ----------
# Reads credentials from a local .env file (never committed to GitHub)
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432),
    "dbname": os.getenv("DB_NAME", "sih_darkweb"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
print("Connected to database.")

# ---------- 2. CREATE DATASET RECORDS (one row per file, for tracking) ----------
def create_dataset_entry(file_name, dataset_type):
    cur.execute(
        """INSERT INTO datasets (file_name, dataset_type, status)
           VALUES (%s, %s, 'processed') RETURNING dataset_id""",
        (file_name, dataset_type),
    )
    return cur.fetchone()[0]

master_dataset_id = create_dataset_entry("SIH26151_darkweb_master_dataset_CLEANED.csv", "forum_posts")
correlation_dataset_id = create_dataset_entry("correlation_feature_matrix.csv", "actor_features")
persona_dataset_id = create_dataset_entry("persona_profiles_CLEANED.json", "persona_profiles")
conn.commit()
print("Dataset entries created.")

# ---------- 3. LOAD correlation_feature_matrix.csv -> actors ----------
cf = pd.read_csv("correlation_feature_matrix.csv")

for _, row in cf.iterrows():
    cur.execute(
        """INSERT INTO actors
           (actor_id, username, post_count, total_words, avg_word_count,
            avg_sentence_length, avg_punctuation, avg_uppercase_ratio,
            avg_digit_count, forums_used, topics_used, dataset_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (actor_id) DO NOTHING""",
        (
            int(row["user_id"]), row["username"], int(row["post_count"]),
            int(row["total_words"]), float(row["avg_word_count"]),
            float(row["avg_sentence_length"]), float(row["avg_punctuation"]),
            float(row["avg_uppercase_ratio"]), float(row["avg_digit_count"]),
            int(row["forums_used"]), int(row["topics_used"]), correlation_dataset_id,
        ),
    )
conn.commit()
print(f"Loaded {len(cf)} actors from correlation_feature_matrix.csv")

# ---------- 4. LOAD persona_profiles_CLEANED.json -> update actors + entities ----------
with open("persona_profiles_CLEANED.json") as f:
    personas = json.load(f)

entity_count = 0
for p in personas:
    actor_id = int(p["user_id"])

    # Update actor with first_seen/last_seen/data_quality_flag
    cur.execute(
        """UPDATE actors
           SET first_seen = %s, last_seen = %s, data_quality_flag = %s
           WHERE actor_id = %s""",
        (p.get("first_seen"), p.get("last_seen"), p.get("data_quality_flag"), actor_id),
    )

    # Split multi-value fields into separate entity rows
    field_map = {
        "emails": "email",
        "onion_addresses": "onion",
        "pgp_fingerprints": "pgp",
    }
    for field, entity_type in field_map.items():
        raw = p.get(field, "")
        if raw and isinstance(raw, str):
            values = [v.strip() for v in raw.split(",") if v.strip()]
            for v in values:
                cur.execute(
                    """INSERT INTO entities (actor_id, entity_type, value, source_dataset_id)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (entity_type, value, actor_id) DO NOTHING""",
                    (actor_id, entity_type, v, persona_dataset_id),
                )
                entity_count += 1

conn.commit()
print(f"Updated {len(personas)} actors and inserted {entity_count} entities from persona_profiles.")

# ---------- 5. LOAD master dataset CSV -> dataset_records ----------
md = pd.read_csv("SIH26151_darkweb_master_dataset_CLEANED.csv")

def clean_val(v):
    """Convert pandas NaN to None for SQL NULL."""
    if pd.isna(v):
        return None
    return v

loaded = 0
for _, row in md.iterrows():
    cur.execute(
        """INSERT INTO dataset_records
           (post_id, actor_id, post_text, "timestamp", forum_id, forum_name,
            topic_id, topic_title, category, source, thread_id,
            reply_to_post_id, reply_to_post_id_status, listing_id, listing_title,
            language, word_count, avg_sentence_length, punctuation_count,
            posting_hour, dataset_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (post_id) DO NOTHING""",
        (
            clean_val(row.get("post_id")), clean_val(row.get("user_id")),
            clean_val(row.get("post_text")), clean_val(row.get("timestamp")),
            clean_val(row.get("forum_id")), clean_val(row.get("forum_name")),
            clean_val(row.get("topic_id")), clean_val(row.get("topic_title")),
            clean_val(row.get("category")), clean_val(row.get("source")),
            clean_val(row.get("thread_id")), clean_val(row.get("reply_to_post_id")),
            clean_val(row.get("reply_to_post_id_status")), clean_val(row.get("listing_id")),
            clean_val(row.get("listing_title")), clean_val(row.get("language")),
            clean_val(row.get("word_count")), clean_val(row.get("avg_sentence_length")),
            clean_val(row.get("punctuation_count")), clean_val(row.get("posting_hour")),
            master_dataset_id,
        ),
    )
    loaded += 1

conn.commit()
print(f"Loaded {loaded} rows into dataset_records.")

cur.close()
conn.close()
print("\nAll done! Data successfully loaded into sih_darkweb.")
