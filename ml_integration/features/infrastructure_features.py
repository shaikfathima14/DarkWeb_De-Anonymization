from typing import List, Set
from models.actor_profile import ActorProfile
from models.evidence import Evidence

class InfrastructureComparator:
    """
    Compares IP/TLS fingerprints and sanitized network fingerprints.
    Down-weights shared infrastructure values to prevent artificial score inflation.
    """

    # Example common/shared services that receive lower quality/evidentiary weight
    COMMON_SHARED_SERVICES: Set[str] = {
        "tor_exit_node_default",
        "cloudflare_shared_ip",
        "public_vpn_endpoint",
    }

    @classmethod
    def compare_infrastructure(cls, actor_a: ActorProfile, actor_b: ActorProfile) -> Evidence:
        net_a = set(actor_a.infrastructure.tls_fingerprints + actor_a.infrastructure.sanitized_network_fingerprints)
        net_b = set(actor_b.infrastructure.tls_fingerprints + actor_b.infrastructure.sanitized_network_fingerprints)

        sources = list(set(actor_a.sources + actor_b.sources))
        ev_id = f"EV-INFRA-{actor_a.actor_id}-{actor_b.actor_id}"

        if not net_a or not net_b:
            return Evidence(
                evidence_id=ev_id,
                type="INFRASTRUCTURE",
                status="UNKNOWN",
                similarity=0.0,
                quality=0.0,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="Infrastructure fingerprints unavailable for one or both profiles.",
            )

        intersection = net_a.intersection(net_b)

        if not intersection:
            return Evidence(
                evidence_id=ev_id,
                type="INFRASTRUCTURE",
                status="NO_MATCH",
                similarity=0.0,
                quality=0.60,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="No infrastructure fingerprint overlap observed.",
            )

        matched_items = list(intersection)
        has_common = any(item in cls.COMMON_SHARED_SERVICES for item in matched_items)

        if has_common:
            # Down-weighted evidentiary strength for shared services
            quality = 0.35
            explanation = f"Matched infrastructure value ({matched_items[0]}) is a known shared/common service. Down-weighted evidentiary weight applied."
            status = "PARTIAL_MATCH"
        else:
            quality = 0.85
            explanation = f"Matching discriminative infrastructure fingerprint: {matched_items[0]}."
            status = "MATCH"

        return Evidence(
            evidence_id=ev_id,
            type="INFRASTRUCTURE",
            status=status,
            similarity=1.0,
            quality=quality,
            actor_a=actor_a.actor_id,
            actor_b=actor_b.actor_id,
            sources=sources,
            independent=not has_common,
            explanation=explanation,
        )
