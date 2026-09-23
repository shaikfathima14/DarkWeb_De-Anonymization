import os
import yaml
from typing import List, Dict, Any, Optional
from models.actor_profile import ActorProfile
from models.evidence import Evidence
from models.result import CorrelationResult, ThreatRisk
from features.identifier_features import IdentifierComparator
from features.stylometric_features import StylometryComparator
from features.activity_features import ActivityComparator
from features.infrastructure_features import InfrastructureComparator
from scoring.coverage import CoverageCalculator
from scoring.redundancy import RedundancyAdjuster
from scoring.risk import RiskAssessor

class WeightedScorer:
    """
    Computes transparent, reconstructable correlation index and decision label.
    """

    DEFAULT_WEIGHTS = {
        "pgp": 0.30,
        "wallet": 0.25,
        "stylometry": 0.20,
        "activity": 0.15,
        "infrastructure": 0.10,
    }

    def __init__(self, config_path: Optional[str] = None):
        self.weights = self.DEFAULT_WEIGHTS.copy()
        self.version = "1.0"
        self.supported_min = 60.0
        self.insufficient_cov_max = 0.30

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    cfg = yaml.safe_load(f)
                    if cfg and "weights" in cfg:
                        self.weights = cfg["weights"]
                    if cfg and "version" in cfg:
                        self.version = str(cfg["version"])
                    if cfg and "thresholds" in cfg:
                        self.supported_min = cfg["thresholds"].get("supported_correlation_min", 60.0)
                        self.insufficient_cov_max = cfg["thresholds"].get("insufficient_coverage_max", 0.30)
            except Exception:
                pass

    def evaluate_pair(self, actor_a: ActorProfile, actor_b: ActorProfile, threat_facts: Optional[List[Dict[str, Any]]] = None) -> CorrelationResult:
        # 1. Run all 5 comparators
        raw_evidence = [
            IdentifierComparator.compare_pgp(actor_a, actor_b),
            IdentifierComparator.compare_wallets(actor_a, actor_b),
            IdentifierComparator.compare_emails(actor_a, actor_b),
            StylometryComparator.compare_stylometry(actor_a, actor_b),
            ActivityComparator.compare_activity(actor_a, actor_b),
            InfrastructureComparator.compare_infrastructure(actor_a, actor_b),
        ]


        # 2. Apply redundancy adjustments
        adjusted_evidence = RedundancyAdjuster.adjust_evidence(raw_evidence)

        # 3. Calculate reconstructable contributions
        total_score = 0.0
        total_weight_applied = 0.0
        processed_evidence = []
        limitations = []

        for ev in adjusted_evidence:
            weight_key = ev.type.lower()
            w = self.weights.get(weight_key, 0.10)

            if ev.status in ("MATCH", "PARTIAL_MATCH"):
                contribution = ev.similarity * ev.quality * w * 100.0
            elif ev.status == "NO_MATCH":
                # Mismatch reduces contribution
                contribution = -1.0 * (1.0 - ev.similarity) * ev.quality * w * 50.0
            else:
                # UNKNOWN or INSUFFICIENT_DATA does not add negative contribution
                contribution = 0.0
                if ev.status == "INSUFFICIENT_DATA":
                    limitations.append(f"{ev.type}: {ev.explanation}")

            ev.contribution = round(contribution, 2)
            processed_evidence.append(ev)

            if ev.status in ("MATCH", "PARTIAL_MATCH", "NO_MATCH"):
                total_score += contribution
                total_weight_applied += w

        # Rescale correlation index to 0.0 - 100.0 range
        correlation_index = max(0.0, min(100.0, total_score))

        # 4. Coverage calculation
        coverage = CoverageCalculator.calculate_coverage(processed_evidence)

        # 5. Decision logic
        if coverage <= self.insufficient_cov_max and correlation_index < self.supported_min:
            decision = "INSUFFICIENT_EVIDENCE"
        elif correlation_index >= self.supported_min:
            decision = "SUPPORTED_CORRELATION"
        else:
            decision = "LOW_CORRELATION"

        # 6. Separate threat risk assessment
        risk = RiskAssessor.assess_risk(threat_facts)

        return CorrelationResult(
            actor_a=actor_a.actor_id,
            actor_b=actor_b.actor_id,
            correlation_index=round(correlation_index, 2),
            decision=decision,
            evidence_coverage=coverage,
            risk=risk,
            evidence=processed_evidence,
            limitations=limitations,
            scoring_version=self.version,
        )
