"""
SIH26151 - Build and load the Neo4j graph
Run this AFTER installing the neo4j driver: pip install neo4j

Before running:
1. Make sure your Neo4j 'neo' instance is RUNNING in Neo4j Desktop.
2. Put this script in the SAME FOLDER as:
   - SIH26151_darkweb_master_dataset_CLEANED.csv  (1998-row version)
   - correlation_feature_matrix.csv
   - persona_profiles_CLEANED.json
3. Update NEO4J_PASSWORD below with your real Neo4j password.
"""

from neo4j import GraphDatabase
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "CHANGE_ME")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
print("Connected to Neo4j.")

# ---------- 1. CONSTRAINTS (uniqueness, also creates indexes) ----------
constraints = [
    "CREATE CONSTRAINT actor_id IF NOT EXISTS FOR (a:Actor) REQUIRE a.actor_id IS UNIQUE",
    "CREATE CONSTRAINT post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.post_id IS UNIQUE",
    "CREATE CONSTRAINT platform_id IF NOT EXISTS FOR (pl:Platform) REQUIRE pl.forum_id IS UNIQUE",
    "CREATE CONSTRAINT pgp_value IF NOT EXISTS FOR (e:PGP) REQUIRE e.value IS UNIQUE",
    "CREATE CONSTRAINT wallet_value IF NOT EXISTS FOR (e:Wallet) REQUIRE e.value IS UNIQUE",
    "CREATE CONSTRAINT email_value IF NOT EXISTS FOR (e:Email) REQUIRE e.value IS UNIQUE",
    "CREATE CONSTRAINT infra_value IF NOT EXISTS FOR (e:Infrastructure) REQUIRE e.value IS UNIQUE",
]

with driver.session() as session:
    for c in constraints:
        session.run(c)
print("Constraints created.")

# ---------- 2. LOAD ACTORS from correlation_feature_matrix.csv ----------
cf = pd.read_csv("correlation_feature_matrix.csv")
actor_rows = cf.to_dict("records")

with driver.session() as session:
    session.run(
        """
        UNWIND $rows AS row
        MERGE (a:Actor {actor_id: row.user_id})
        SET a.username = row.username,
            a.post_count = row.post_count,
            a.total_words = row.total_words,
            a.avg_word_count = row.avg_word_count,
            a.avg_sentence_length = row.avg_sentence_length,
            a.avg_punctuation = row.avg_punctuation,
            a.avg_uppercase_ratio = row.avg_uppercase_ratio,
            a.avg_digit_count = row.avg_digit_count,
            a.forums_used = row.forums_used,
            a.topics_used = row.topics_used
        """,
        rows=actor_rows,
    )
print(f"Loaded {len(actor_rows)} Actor nodes.")

# ---------- 3. ENRICH ACTORS from persona_profiles_CLEANED.json ----------
with open("persona_profiles_CLEANED.json") as f:
    personas = json.load(f)

persona_rows = [
    {
        "actor_id": p["user_id"],
        "first_seen": p.get("first_seen"),
        "last_seen": p.get("last_seen"),
        "data_quality_flag": p.get("data_quality_flag"),
    }
    for p in personas
]

with driver.session() as session:
    session.run(
        """
        UNWIND $rows AS row
        MATCH (a:Actor {actor_id: row.actor_id})
        SET a.first_seen = row.first_seen,
            a.last_seen = row.last_seen,
            a.data_quality_flag = row.data_quality_flag
        """,
        rows=persona_rows,
    )
print(f"Enriched {len(persona_rows)} Actor nodes with first_seen/last_seen/data_quality_flag.")

# ---------- 4. LOAD MASTER DATASET: Posts, Platforms, Entities, Replies ----------
md = pd.read_csv("SIH26151_darkweb_master_dataset_CLEANED.csv")

def clean(v):
    if pd.isna(v):
        return None
    return v

post_rows = []
for _, row in md.iterrows():
    post_rows.append({
        "post_id": clean(row.get("post_id")),
        "actor_id": clean(row.get("user_id")),
        "forum_id": clean(row.get("forum_id")),
        "forum_name": clean(row.get("forum_name")),
        "category": clean(row.get("category")),
        "timestamp": clean(row.get("timestamp")),
        "word_count": clean(row.get("word_count")),
        "posting_hour": clean(row.get("posting_hour")),
        "pgp": clean(row.get("pgp_fingerprint")),
        "wallet": clean(row.get("wallet_id")),
        "email": clean(row.get("email_like_identifier")),
        "onion": clean(row.get("onion_address")),
        "ip_tls": clean(row.get("ip_tls_fingerprint")),
        "reply_to_post_id": clean(row.get("reply_to_post_id")),
        "reply_status": clean(row.get("reply_to_post_id_status")),
    })

with driver.session() as session:
    # Posts + POSTED_IN (Actor -> Post)
    session.run(
        """
        UNWIND $rows AS row
        MERGE (p:Post {post_id: row.post_id})
        SET p.category = row.category,
            p.timestamp = row.timestamp,
            p.word_count = row.word_count,
            p.posting_hour = row.posting_hour
        WITH p, row
        MATCH (a:Actor {actor_id: row.actor_id})
        MERGE (a)-[:POSTED]->(p)
        """,
        rows=post_rows,
    )
    print("Posts created and linked to Actors.")

    # Platforms + POSTED_ON (Post -> Platform)
    session.run(
        """
        UNWIND $rows AS row
        WITH row WHERE row.forum_id IS NOT NULL
        MERGE (pl:Platform {forum_id: row.forum_id})
        SET pl.forum_name = row.forum_name
        WITH pl, row
        MATCH (p:Post {post_id: row.post_id})
        MERGE (p)-[:POSTED_ON]->(pl)
        """,
        rows=post_rows,
    )
    print("Platforms created and linked.")

    # PGP entities + USES (Actor -> PGP)
    session.run(
        """
        UNWIND $rows AS row
        WITH row WHERE row.pgp IS NOT NULL
        MERGE (e:PGP {value: row.pgp})
        WITH e, row
        MATCH (a:Actor {actor_id: row.actor_id})
        MERGE (a)-[:USES]->(e)
        """,
        rows=post_rows,
    )
    print("PGP entities linked.")

    # Wallet entities + USES
    session.run(
        """
        UNWIND $rows AS row
        WITH row WHERE row.wallet IS NOT NULL
        MERGE (e:Wallet {value: row.wallet})
        WITH e, row
        MATCH (a:Actor {actor_id: row.actor_id})
        MERGE (a)-[:USES]->(e)
        """,
        rows=post_rows,
    )
    print("Wallet entities linked.")

    # Email entities + USES
    session.run(
        """
        UNWIND $rows AS row
        WITH row WHERE row.email IS NOT NULL
        MERGE (e:Email {value: row.email})
        WITH e, row
        MATCH (a:Actor {actor_id: row.actor_id})
        MERGE (a)-[:USES]->(e)
        """,
        rows=post_rows,
    )
    print("Email entities linked.")

    # Infrastructure entities (onion) + USES
    session.run(
        """
        UNWIND $rows AS row
        WITH row WHERE row.onion IS NOT NULL
        MERGE (e:Infrastructure {value: row.onion})
        SET e.type = 'onion'
        WITH e, row
        MATCH (a:Actor {actor_id: row.actor_id})
        MERGE (a)-[:USES]->(e)
        """,
        rows=post_rows,
    )
    print("Onion infrastructure entities linked.")

    # Infrastructure entities (ip_tls) + USES
    session.run(
        """
        UNWIND $rows AS row
        WITH row WHERE row.ip_tls IS NOT NULL
        MERGE (e:Infrastructure {value: row.ip_tls})
        SET e.type = 'ip_tls'
        WITH e, row
        MATCH (a:Actor {actor_id: row.actor_id})
        MERGE (a)-[:USES]->(e)
        """,
        rows=post_rows,
    )
    print("IP/TLS infrastructure entities linked.")

    # REPLIED_TO (Post -> Post), only where status is 'valid'
    reply_rows = [r for r in post_rows if r["reply_status"] == "valid" and r["reply_to_post_id"] is not None]
    session.run(
        """
        UNWIND $rows AS row
        MATCH (p1:Post {post_id: row.post_id})
        MATCH (p2:Post {post_id: toInteger(row.reply_to_post_id)})
        MERGE (p1)-[:REPLIED_TO]->(p2)
        """,
        rows=reply_rows,
    )
    print(f"Created {len(reply_rows)} REPLIED_TO relationships.")

print("\nAll done! Neo4j graph successfully built and loaded.")
driver.close()
