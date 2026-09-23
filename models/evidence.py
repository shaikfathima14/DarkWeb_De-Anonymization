from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Evidence:
    evidence_id: str
    type: str  # PGP, WALLET, STYLOMETRY, ACTIVITY, INFRASTRUCTURE
    status: str  # MATCH, PARTIAL_MATCH, NO_MATCH, UNKNOWN, INSUFFICIENT_DATA
    similarity: float  # 0.0 to 1.0
    quality: float  # 0.0 to 1.0 (evidentiary strength)
    actor_a: str
    actor_b: str
    sources: List[str] = field(default_factory=list)
    independent: bool = True
    explanation: str = ""
    contribution: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "type": self.type,
            "status": self.status,
            "similarity": round(self.similarity, 4),
            "quality": round(self.quality, 4),
            "actor_a": self.actor_a,
            "actor_b": self.actor_b,
            "sources": self.sources,
            "independent": self.independent,
            "explanation": self.explanation,
            "contribution": round(self.contribution, 2),
        }
