from typing import List
from models.evidence import Evidence

class RedundancyAdjuster:
    """
    Adjusts quality/contribution for duplicate records or non-independent evidence
    to prevent artificial score multiplication.
    """

    @staticmethod
    def adjust_evidence(evidence_list: List[Evidence]) -> List[Evidence]:
        seen_types = set()
        adjusted = []

        for ev in evidence_list:
            ev_copy = Evidence(
                evidence_id=ev.evidence_id,
                type=ev.type,
                status=ev.status,
                similarity=ev.similarity,
                quality=ev.quality,
                actor_a=ev.actor_a,
                actor_b=ev.actor_b,
                sources=ev.sources,
                independent=ev.independent,
                explanation=ev.explanation,
                contribution=ev.contribution,
            )

            # If multiple evidence items of the same type exist, mark non-primary as dependent
            if ev.type in seen_types:
                ev_copy.independent = False
                ev_copy.quality *= 0.50  # Apply 50% discount for redundant duplicate evidence
                ev_copy.explanation += " (Redundant evidence penalty applied)."
            else:
                seen_types.add(ev.type)

            adjusted.append(ev_copy)

        return adjusted
