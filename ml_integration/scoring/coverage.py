from typing import List
from models.evidence import Evidence

class CoverageCalculator:
    """
    Calculates evidence coverage ratio across the 5 standard comparator domains:
    PGP, WALLET, STYLOMETRY, ACTIVITY, INFRASTRUCTURE.
    """

    TOTAL_DOMAINS = 5

    @classmethod
    def calculate_coverage(cls, evidence_list: List[Evidence]) -> float:
        valid_domains = set()
        for ev in evidence_list:
            if ev.status in ("MATCH", "PARTIAL_MATCH", "NO_MATCH"):
                valid_domains.add(ev.type.upper())
        return len(valid_domains) / float(cls.TOTAL_DOMAINS)
