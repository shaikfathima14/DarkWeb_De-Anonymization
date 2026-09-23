from typing import List, Dict, Any, Optional
from models.result import ThreatRisk

class RiskAssessor:
    """
    Assesses threat risk separately from correlation index.
    Returns UNKNOWN when supported threat facts are absent.
    """

    @staticmethod
    def assess_risk(threat_facts: Optional[List[Dict[str, Any]]] = None) -> ThreatRisk:
        if not threat_facts:
            return ThreatRisk(
                level="UNKNOWN",
                status="INSUFFICIENT_THREAT_FACTS",
                threat_indicators=[],
            )

        indicators = []
        severity_score = 0

        for fact in threat_facts:
            category = fact.get("category", "").lower()
            severity = fact.get("severity", "LOW").upper()
            indicators.append(f"{category}:{severity}")

            if severity == "CRITICAL":
                severity_score += 4
            elif severity == "HIGH":
                severity_score += 3
            elif severity == "MEDIUM":
                severity_score += 2
            else:
                severity_score += 1

        if severity_score >= 8:
            level = "CRITICAL"
        elif severity_score >= 5:
            level = "HIGH"
        elif severity_score >= 3:
            level = "MEDIUM"
        else:
            level = "LOW"

        return ThreatRisk(
            level=level,
            status="SUPPORTED_THREAT_FACTS",
            threat_indicators=indicators,
        )
