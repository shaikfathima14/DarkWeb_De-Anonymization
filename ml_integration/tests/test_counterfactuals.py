import pytest
from models.actor_profile import ActorProfile, Identifiers, Stylometry
from scoring.weighted_scorer import WeightedScorer
from scoring.counterfactual import CounterfactualEngine

def test_counterfactual_recalculation():
    a = ActorProfile(
        actor_id="ACTOR_A",
        identifiers=Identifiers(pgp=["KEY_MATCH"], wallets=["W_MATCH"]),
        stylometry=Stylometry(document_count=10, avg_sentence_length=15.0),
    )
    b = ActorProfile(
        actor_id="ACTOR_B",
        identifiers=Identifiers(pgp=["KEY_MATCH"], wallets=["W_MATCH"]),
        stylometry=Stylometry(document_count=10, avg_sentence_length=15.0),
    )

    scorer = WeightedScorer()
    baseline_result = scorer.evaluate_pair(a, b)

    # Recalculate without PGP
    cf_pgp = CounterfactualEngine.recalculate_without(baseline_result, exclude_target="PGP")

    assert cf_pgp.baseline_score == baseline_result.correlation_index
    assert cf_pgp.counterfactual_score < baseline_result.correlation_index
    assert cf_pgp.difference > 0.0
    assert "EV-PGP-ACTOR_A-ACTOR_B" in cf_pgp.excluded_evidence
