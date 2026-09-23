from dataclasses import dataclass, field
from typing import List, Dict, Any
from models.evidence import Evidence

@dataclass
class ThreatRisk:
    level: str = "UNKNOWN"  # LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN
    status: str = "INSUFFICIENT_THREAT_FACTS"
    threat_indicators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "status": self.status,
            "threat_indicators": self.threat_indicators,
        }

@dataclass
class CorrelationResult:
    actor_a: str
    actor_b: str
    correlation_index: float
    decision: str  # SUPPORTED_CORRELATION, LOW_CORRELATION, INSUFFICIENT_EVIDENCE
    evidence_coverage: float
    risk: ThreatRisk = field(default_factory=ThreatRisk)
    evidence: List[Evidence] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    scoring_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_a": self.actor_a,
            "actor_b": self.actor_b,
            "correlation_index": round(self.correlation_index, 2),
            "decision": self.decision,
            "evidence_coverage": round(self.evidence_coverage, 4),
            "risk": self.risk.to_dict(),
            "evidence": [e.to_dict() for e in self.evidence],
            "limitations": self.limitations,
            "scoring_version": self.scoring_version,
        }

@dataclass
class CounterfactualResult:
    baseline_score: float
    counterfactual_score: float
    difference: float
    excluded_evidence: List[str]
    remaining_evidence: List[Dict[str, Any]]
    changed_decision: bool
    baseline_decision: str
    counterfactual_decision: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_score": round(self.baseline_score, 2),
            "counterfactual_score": round(self.counterfactual_score, 2),
            "difference": round(self.difference, 2),
            "excluded_evidence": self.excluded_evidence,
            "remaining_evidence": self.remaining_evidence,
            "changed_decision": self.changed_decision,
            "baseline_decision": self.baseline_decision,
            "counterfactual_decision": self.counterfactual_decision,
        }
