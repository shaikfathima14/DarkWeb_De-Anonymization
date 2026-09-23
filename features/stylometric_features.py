import math
from models.actor_profile import ActorProfile
from models.evidence import Evidence

class StylometryComparator:
    """
    Compares NLP & stylometric features across two actor profiles.
    Returns INSUFFICIENT_DATA if document count or text volume is low.
    """

    MIN_DOC_COUNT = 3  # Minimum post/doc count required for valid stylometry

    @classmethod
    def compare_stylometry(cls, actor_a: ActorProfile, actor_b: ActorProfile) -> Evidence:
        sources = list(set(actor_a.sources + actor_b.sources))
        ev_id = f"EV-STYLO-{actor_a.actor_id}-{actor_b.actor_id}"

        # 1. Check volume threshold
        if (actor_a.stylometry.document_count < cls.MIN_DOC_COUNT or
                actor_b.stylometry.document_count < cls.MIN_DOC_COUNT):
            return Evidence(
                evidence_id=ev_id,
                type="STYLOMETRY",
                status="INSUFFICIENT_DATA",
                similarity=0.0,
                quality=0.0,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="Insufficient text volume to perform reliable stylometric comparison.",
            )

        # 2. Compare features if available
        len_a = actor_a.stylometry.avg_sentence_length
        len_b = actor_b.stylometry.avg_sentence_length

        punct_a = actor_a.stylometry.punctuation_rate
        punct_b = actor_b.stylometry.punctuation_rate

        div_a = actor_a.stylometry.vocabulary_diversity
        div_b = actor_b.stylometry.vocabulary_diversity

        if len_a is None or len_b is None:
            return Evidence(
                evidence_id=ev_id,
                type="STYLOMETRY",
                status="UNKNOWN",
                similarity=0.0,
                quality=0.0,
                actor_a=actor_a.actor_id,
                actor_b=actor_b.actor_id,
                sources=sources,
                independent=True,
                explanation="Stylometric metrics absent from profile.",
            )

        # Feature difference scoring
        len_diff = abs(len_a - len_b) / (max(len_a, len_b) + 1e-5)
        punct_diff = abs((punct_a or 0) - (punct_b or 0)) / (max(punct_a or 1, punct_b or 1) + 1e-5)
        div_diff = abs((div_a or 0) - (div_b or 0)) / (max(div_a or 1, div_b or 1) + 1e-5)

        avg_diff = (len_diff + punct_diff + div_diff) / 3.0
        similarity = max(0.0, 1.0 - avg_diff)

        # Evidentiary quality increases with document volume
        quality = min(0.85, 0.4 + 0.05 * min(actor_a.stylometry.document_count, actor_b.stylometry.document_count))

        if similarity > 0.75:
            status = "MATCH"
            explanation = f"High stylometric feature similarity ({round(similarity*100, 1)}%) across sentence structure and vocabulary."
        elif similarity > 0.45:
            status = "PARTIAL_MATCH"
            explanation = f"Moderate stylometric feature similarity ({round(similarity*100, 1)}%)."
        else:
            status = "NO_MATCH"
            explanation = f"Distinct stylometric signature observed (similarity {round(similarity*100, 1)}%)."

        return Evidence(
            evidence_id=ev_id,
            type="STYLOMETRY",
            status=status,
            similarity=similarity,
            quality=quality,
            actor_a=actor_a.actor_id,
            actor_b=actor_b.actor_id,
            sources=sources,
            independent=True,
            explanation=explanation,
        )
