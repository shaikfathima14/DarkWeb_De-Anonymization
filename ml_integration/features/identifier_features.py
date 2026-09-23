from typing import Optional, List
from models.actor_profile import ActorProfile
from models.evidence import Evidence

class IdentifierComparator:
    """
    Compares PGP fingerprints and Cryptocurrency Wallet IDs between two profiles.
    """

    @staticmethod
    def compare_pgp(actor_a: ActorProfile, actor_b: ActorProfile) -> Evidence:
        pgp_a = set(actor_a.identifiers.pgp)
        pgp_b = set(actor_b.identifiers.pgp)

        sources = list(set(actor_a.sources + actor_b.sources))

        if not pgp_a or not pgp_b:
            return Evidence(
                evidence_id=f"EV-PGP-{actor_a.actor_id}-{actor_b.actor_id}",
                type="PGP",
                status="UNKNOWN",
                similarity=0.0,
                quality=0.0,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="PGP fingerprint unavailable for one or both profiles.",
            )

        intersection = pgp_a.intersection(pgp_b)
        if intersection:
            matched_key = list(intersection)[0]
            return Evidence(
                evidence_id=f"EV-PGP-{actor_a.actor_id}-{actor_b.actor_id}",
                type="PGP",
                status="MATCH",
                similarity=1.0,
                quality=0.95,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation=f"Matching PGP key observed: {matched_key}.",
            )

        return Evidence(
            evidence_id=f"EV-PGP-{actor_a.actor_id}-{actor_b.actor_id}",
            type="PGP",
            status="NO_MATCH",
            similarity=0.0,
            quality=0.90,
            actor_a=actor_a.actor_id,
            actor_b=actor_b.actor_id,
            sources=sources,
            independent=True,
            explanation="Different PGP fingerprints published across profiles.",
        )

    @staticmethod
    def compare_wallets(actor_a: ActorProfile, actor_b: ActorProfile) -> Evidence:
        wallets_a = set(actor_a.identifiers.wallets)
        wallets_b = set(actor_b.identifiers.wallets)

        sources = list(set(actor_a.sources + actor_b.sources))

        if not wallets_a or not wallets_b:
            return Evidence(
                evidence_id=f"EV-WALLET-{actor_a.actor_id}-{actor_b.actor_id}",
                type="WALLET",
                status="UNKNOWN",
                similarity=0.0,
                quality=0.0,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="Wallet address unavailable for one or both profiles.",
            )

        intersection = wallets_a.intersection(wallets_b)
        if intersection:
            matched_wallet = list(intersection)[0]
            return Evidence(
                evidence_id=f"EV-WALLET-{actor_a.actor_id}-{actor_b.actor_id}",
                type="WALLET",
                status="MATCH",
                similarity=1.0,
                quality=0.90,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation=f"Matching crypto wallet observed: {matched_wallet}.",
            )

        return Evidence(
            evidence_id=f"EV-WALLET-{actor_a.actor_id}-{actor_b.actor_id}",
            type="WALLET",
            status="NO_MATCH",
            similarity=0.0,
            quality=0.85,
            actor_a=actor_a.actor_id,
            actor_b=actor_b.actor_id,
            sources=sources,
            independent=True,
            explanation="Different wallet addresses observed without overlap.",
        )

    @staticmethod
    def compare_emails(actor_a: ActorProfile, actor_b: ActorProfile) -> Evidence:
        emails_a = set(actor_a.identifiers.emails)
        emails_b = set(actor_b.identifiers.emails)

        sources = list(set(actor_a.sources + actor_b.sources))

        if not emails_a or not emails_b:
            return Evidence(
                evidence_id=f"EV-EMAIL-{actor_a.actor_id}-{actor_b.actor_id}",
                type="EMAIL",
                status="UNKNOWN",
                similarity=0.0,
                quality=0.0,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="Email-like identifier unavailable for one or both profiles.",
            )

        intersection = emails_a.intersection(emails_b)
        if intersection:
            matched_email = list(intersection)[0]
            return Evidence(
                evidence_id=f"EV-EMAIL-{actor_a.actor_id}-{actor_b.actor_id}",
                type="EMAIL",
                status="MATCH",
                similarity=1.0,
                quality=0.90,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation=f"Matching contact email observed: {matched_email}.",
            )

        return Evidence(
            evidence_id=f"EV-EMAIL-{actor_a.actor_id}-{actor_b.actor_id}",
            type="EMAIL",
            status="NO_MATCH",
            similarity=0.0,
            quality=0.80,
            actor_a=actor_a.actor_id,
            actor_b=actor_b.actor_id,
            sources=sources,
            independent=True,
            explanation="Different contact emails published across profiles.",
        )

