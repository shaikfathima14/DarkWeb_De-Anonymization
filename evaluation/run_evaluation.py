import time
import copy
from typing import List, Tuple, Dict, Any
from models.actor_profile import ActorProfile
from scoring.weighted_scorer import WeightedScorer
from evaluation.metrics import MetricsCalculator, EvaluationMetrics

class LeakageControlledEvaluator:
    """
    Day 4 — Held-Out Evaluation with Leakage Control.
    Masks deterministic identifiers (e.g. user_id derived synthetic tags)
    to measure true generalization performance.
    """

    def __init__(self, scorer: WeightedScorer):
        self.scorer = scorer

    def evaluate(
        self,
        positive_pairs: List[Tuple[ActorProfile, ActorProfile]],
        negative_pairs: List[Tuple[ActorProfile, ActorProfile]],
        mask_deterministic: bool = True
    ) -> EvaluationMetrics:
        y_true = []
        y_pred = []
        latencies = []

        # Process positive pairs (ground truth: same identity = True)
        for actor_a, actor_b in positive_pairs:
            a_eval, b_eval = self._prepare_eval_profiles(actor_a, actor_b, mask_deterministic)
            t0 = time.perf_counter()
            res = self.scorer.evaluate_pair(a_eval, b_eval)
            lat_ms = (time.perf_counter() - t0) * 1000.0

            y_true.append(True)
            y_pred.append(res.decision)
            latencies.append(lat_ms)

        # Process negative pairs (ground truth: different identity = False)
        for actor_a, actor_b in negative_pairs:
            a_eval, b_eval = self._prepare_eval_profiles(actor_a, actor_b, mask_deterministic)
            t0 = time.perf_counter()
            res = self.scorer.evaluate_pair(a_eval, b_eval)
            lat_ms = (time.perf_counter() - t0) * 1000.0

            y_true.append(False)
            y_pred.append(res.decision)
            latencies.append(lat_ms)

        return MetricsCalculator.compute(y_true, y_pred, latencies)

    def _prepare_eval_profiles(
        self,
        a: ActorProfile,
        b: ActorProfile,
        mask_deterministic: bool
    ) -> Tuple[ActorProfile, ActorProfile]:
        a_copy = copy.deepcopy(a)
        b_copy = copy.deepcopy(b)

        if mask_deterministic:
            # Mask deterministic/test-derived identifiers (e.g. usernames containing user_id or test hashes)
            a_copy.identifiers.aliases = [x for x in a_copy.identifiers.aliases if not x.startswith("test_det_")]
            b_copy.identifiers.aliases = [x for x in b_copy.identifiers.aliases if not x.startswith("test_det_")]

        return a_copy, b_copy
