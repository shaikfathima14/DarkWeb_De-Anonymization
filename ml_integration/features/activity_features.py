import math
from typing import List
from models.actor_profile import ActorProfile
from models.evidence import Evidence

class ActivityComparator:
    """
    Compares posting activity temporal patterns (posting hours 0-23).
    """

    @staticmethod
    def compare_activity(actor_a: ActorProfile, actor_b: ActorProfile) -> Evidence:
        hours_a = actor_a.activity.posting_hours
        hours_b = actor_b.activity.posting_hours

        sources = list(set(actor_a.sources + actor_b.sources))
        ev_id = f"EV-ACTIVITY-{actor_a.actor_id}-{actor_b.actor_id}"

        if not hours_a or not hours_b:
            return Evidence(
                evidence_id=ev_id,
                type="ACTIVITY",
                status="UNKNOWN",
                similarity=0.0,
                quality=0.0,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="Posting activity hours unavailable for one or both profiles.",
            )

        # Build 24-hour histogram vectors
        vec_a = [0] * 24
        vec_b = [0] * 24

        for h in hours_a:
            if 0 <= h < 24:
                vec_a[h] += 1
        for h in hours_b:
            if 0 <= h < 24:
                vec_b[h] += 1

        # Calculate Cosine Similarity
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0 or norm_b == 0:
            similarity = 0.0
        else:
            similarity = dot / (norm_a * norm_b)

        quality = 0.70

        if similarity >= 0.70:
            status = "MATCH"
            explanation = f"Strong temporal posting pattern overlap ({round(similarity * 100, 1)}%)."
        elif similarity >= 0.30:
            status = "PARTIAL_MATCH"
            explanation = f"Partial posting hour correlation ({round(similarity * 100, 1)}%)."
        else:
            status = "NO_MATCH"
            explanation = f"Divergent active posting window ({round(similarity * 100, 1)}%)."

        return Evidence(
            evidence_id=ev_id,
            type="ACTIVITY",
            status=status,
            similarity=similarity,
            quality=quality,
            actor_a=actor_a.actor_id,
            actor_b=actor_b.actor_id,
            sources=sources,
            independent=True,
            explanation=explanation,
        )
