import pandas as pd
from typing import Dict, List
import math
from models.actor_profile import ActorProfile, Identifiers, Stylometry, Activity, Infrastructure

class ProfileBuilder:
    """
    Builds standardized ActorProfile objects from CSV dataframe rows
    matching the 27-column SIH26151 dataset format.
    """

    @staticmethod
    def build_profiles_from_df(df: pd.DataFrame) -> Dict[str, ActorProfile]:
        profiles: Dict[str, ActorProfile] = {}

        if "user_id" not in df.columns:
            raise ValueError("CSV must contain 'user_id' column")

        grouped = df.groupby("user_id")

        for user_id, group in grouped:
            actor_id = str(user_id)
            
            # 1. Identifiers
            pgp_keys = set()
            wallets = set()
            emails = set()
            aliases = set()

            for _, row in group.iterrows():
                if pd.notna(row.get("username")):
                    aliases.add(str(row["username"]))
                if pd.notna(row.get("pgp_fingerprint")):
                    pgp_keys.add(str(row["pgp_fingerprint"]))
                if pd.notna(row.get("wallet_id")):
                    wallets.add(str(row["wallet_id"]))
                if pd.notna(row.get("email_like_identifier")):
                    emails.add(str(row["email_like_identifier"]))

            identifiers = Identifiers(
                pgp=sorted(list(pgp_keys)),
                wallets=sorted(list(wallets)),
                emails=sorted(list(emails)),
                aliases=sorted(list(aliases)),
            )

            # 2. Stylometry
            doc_count = len(group)
            total_words = 0
            sentence_lengths = []
            punct_counts = []

            for _, row in group.iterrows():
                if pd.notna(row.get("word_count")):
                    total_words += float(row["word_count"])
                if pd.notna(row.get("avg_sentence_length")):
                    sentence_lengths.append(float(row["avg_sentence_length"]))
                if pd.notna(row.get("punctuation_count")):
                    punct_counts.append(float(row["punctuation_count"]))

            avg_sent_len = (sum(sentence_lengths) / len(sentence_lengths)) if sentence_lengths else None
            avg_punct = (sum(punct_counts) / len(punct_counts)) if punct_counts else None
            # Vocabulary diversity heuristic estimate (unique words / total words)
            vocab_div = round(min(1.0, 50.0 / (total_words + 1e-5)), 4) if total_words > 0 else None

            stylometry = Stylometry(
                language="en",
                document_count=doc_count,
                avg_sentence_length=avg_sent_len,
                vocabulary_diversity=vocab_div,
                punctuation_rate=avg_punct,
                function_word_frequency={},
                phrase_features={},
            )

            # 3. Activity
            posting_hours = []
            for _, row in group.iterrows():
                if pd.notna(row.get("posting_hour")):
                    try:
                        posting_hours.append(int(row["posting_hour"]))
                    except ValueError:
                        pass

            activity = Activity(
                posting_hours=posting_hours,
                weekday_distribution={},
                activity_frequency={"total_posts": doc_count},
            )

            # 4. Infrastructure
            tls = set()
            net = set()
            hosting = set()

            for _, row in group.iterrows():
                if pd.notna(row.get("ip_tls_fingerprint")):
                    tls.add(str(row["ip_tls_fingerprint"]))
                if pd.notna(row.get("onion_address")):
                    net.add(str(row["onion_address"]))

            infrastructure = Infrastructure(
                tls_fingerprints=sorted(list(tls)),
                sanitized_network_fingerprints=sorted(list(net)),
                hosting_identifiers=sorted(list(hosting)),
            )

            # 5. Sources
            sources = sorted(list(set(str(r["source"]) for _, r in group.iterrows() if pd.notna(r.get("source")))))

            profiles[actor_id] = ActorProfile(
                actor_id=actor_id,
                profile_version="1.0",
                identifiers=identifiers,
                stylometry=stylometry,
                activity=activity,
                infrastructure=infrastructure,
                sources=sources if sources else ["SRC-DEFAULT"],
            )

        return profiles
