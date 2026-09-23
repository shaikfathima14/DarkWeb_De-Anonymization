from typing import List, Union, Dict, Any
from models.result import CorrelationResult, CounterfactualResult
from models.evidence import Evidence

class CounterfactualEngine:
    """
    Recalculates correlation score and decision with specified evidence items or evidence types excluded.
    Preserves baseline calculation intact.
    """

    @staticmethod
    def recalculate_without(
        result: CorrelationResult,
        exclude_target: Union[str, List[str]],
        supported_threshold: float = 60.0
    ) -> CounterfactualResult:
        targets = [exclude_target] if isinstance(exclude_target, str) else exclude_target
        targets_lower = set(t.lower() for t in targets)

        baseline_score = result.correlation_index
        baseline_decision = result.decision

        excluded_ids = []
        remaining_evidence = []
        new_total_score = 0.0

        for ev in result.evidence:
            # Check if matching by evidence_id or evidence type (e.g. "PGP", "EV-PGP-001")
            is_excluded = (
                ev.evidence_id.lower() in targets_lower or
                ev.type.lower() in targets_lower
            )

            if is_excluded:
                excluded_ids.append(ev.evidence_id)
            else:
                remaining_evidence.append(ev.to_dict())
                new_total_score += ev.contribution

        counterfactual_score = max(0.0, min(100.0, new_total_score))

        # Counterfactual decision
        if len(remaining_evidence) == 0 or (len(remaining_evidence) <= 1 and counterfactual_score < supported_threshold):
            counterfactual_decision = "INSUFFICIENT_EVIDENCE"
        elif counterfactual_score >= supported_threshold:
            counterfactual_decision = "SUPPORTED_CORRELATION"
        else:
            counterfactual_decision = "LOW_CORRELATION"

        difference = round(baseline_score - counterfactual_score, 2)
        changed_decision = (baseline_decision != counterfactual_decision)

        return CounterfactualResult(
            baseline_score=round(baseline_score, 2),
            counterfactual_score=round(counterfactual_score, 2),
            difference=difference,
            excluded_evidence=excluded_ids if excluded_ids else list(targets),
            remaining_evidence=remaining_evidence,
            changed_decision=changed_decision,
            baseline_decision=baseline_decision,
            counterfactual_decision=counterfactual_decision,
        )
