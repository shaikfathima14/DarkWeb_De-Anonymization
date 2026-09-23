from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class EvaluationMetrics:
    total_pairs: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    abstentions: int  # INSUFFICIENT_EVIDENCE
    precision: float
    recall: float
    f1_score: float
    abstention_coverage: float
    avg_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pairs": self.total_pairs,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "abstentions": self.abstentions,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "abstention_coverage": round(self.abstention_coverage, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }

class MetricsCalculator:
    """
    Computes classification evaluation metrics for correlation predictions against ground truth labels.
    """

    @staticmethod
    def compute(y_true: List[bool], y_pred_decision: List[str], latencies_ms: List[float]) -> EvaluationMetrics:
        tp = fp = tn = fn = abstentions = 0

        for true_same, decision in zip(y_true, y_pred_decision):
            if decision == "INSUFFICIENT_EVIDENCE":
                abstentions += 1
                continue

            pred_same = (decision == "SUPPORTED_CORRELATION")

            if true_same and pred_same:
                tp += 1
            elif not true_same and pred_same:
                fp += 1
            elif not true_same and not pred_same:
                tn += 1
            elif true_same and not pred_same:
                fn += 1

        total = len(y_true)
        evaluated = total - abstentions

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        abstention_coverage = evaluated / total if total > 0 else 0.0
        avg_latency = (sum(latencies_ms) / len(latencies_ms)) if latencies_ms else 0.0

        return EvaluationMetrics(
            total_pairs=total,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            abstentions=abstentions,
            precision=precision,
            recall=recall,
            f1_score=f1,
            abstention_coverage=abstention_coverage,
            avg_latency_ms=avg_latency,
        )
