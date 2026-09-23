import pandas as pd
import random
import os

def generate_sample_csv(output_path: str, num_rows: int = 200, num_users: int = 20):
    """
    Generates a synthetic pandas DataFrame adhering to the 27-column schema of
    SIH26151_darkweb_master_dataset_CLEANED.csv for standalone testing.
    """.strip()

    categories = ["malware", "ransomware", "credentials", "carding", "zero_day"]
    forums = ["Dread", "Exploit.in", "XSS.is", "BreachForums"]

    user_ids = [f"USER_{100 + i}" for i in range(num_users)]
    pgp_keys = {u: f"4A92F{i:03d}B1C88D" for i, u in enumerate(user_ids[:10])}
    wallets = {u: f"bc1qxy{i:03d}z89q23" for i, u in enumerate(user_ids[:12])}
    tls_fps = {u: f"tls_fp_{i:03d}" for i, u in enumerate(user_ids[:15])}

    rows = []

    for i in range(1, num_rows + 1):
        u_id = random.choice(user_ids)
        u_num = int(u_id.split("_")[1])

        # Create some intentional correlation pairs (e.g. USER_100 and USER_101 share PGP/Wallet)
        if u_id == "USER_101" and random.random() > 0.3:
            pgp = pgp_keys.get("USER_100")
            wallet = wallets.get("USER_100")
        else:
            pgp = pgp_keys.get(u_id)
            wallet = wallets.get(u_id)

        row = {
            "post_id": f"POST_{i:04d}",
            "user_id": u_id,
            "username": f"actor_alias_{u_num}",
            "post_text": f"Selling fresh access to enterprise network {i}. PM for PGP info or escrow details.",
            "timestamp": f"2026-09-{(i % 28) + 1:02d}T{(i % 24):02d}:15:00Z",
            "forum_id": f"FORUM_{(i % 4) + 1}",
            "forum_name": forums[i % len(forums)],
            "topic_id": f"TOPIC_{i % 30}",
            "topic_title": f"Enterprise Access {i % 10}",
            "category": categories[i % len(categories)],
            "source": f"SRC-00{(i % 3) + 1}",
            "pgp_fingerprint": pgp if random.random() > 0.4 else None,
            "wallet_id": wallet if random.random() > 0.4 else None,
            "email_like_identifier": f"contact_{u_num}@onionmail.org" if random.random() > 0.5 else None,
            "onion_address": f"darkmarket{u_num % 5}.onion" if random.random() > 0.3 else None,
            "ip_tls_fingerprint": tls_fps.get(u_id) if random.random() > 0.4 else None,
            "thread_id": f"THREAD_{i % 20}",
            "reply_to_post_id": f"POST_{(i - 1):04d}" if i > 1 and random.random() > 0.6 else None,
            "listing_id": f"LIST_{i:03d}" if random.random() > 0.7 else None,
            "listing_title": f"Database Dump {i}" if random.random() > 0.7 else None,
            "language": "en",
            "word_count": random.randint(15, 120),
            "avg_sentence_length": round(random.uniform(8.0, 22.0), 2),
            "punctuation_count": random.randint(2, 15),
            "posting_hour": (i % 24),
            "data_status": "CLEAN",
            "reply_to_post_id_status": "VALID",
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic CSV with {len(df)} rows at: {output_path}")
    return df

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "sample_master_dataset.csv")
    generate_sample_csv(out)
