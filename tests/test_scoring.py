import pytest
from models.actor_profile import ActorProfile, Identifiers, Stylometry, Activity, Infrastructure
from scoring.weighted_scorer import WeightedScorer
from scoring.risk import RiskAssessor

@pytest.fixture
def test_pair():
    a = ActorProfile(
        actor_id="ACTOR_A",
        identifiers=Identifiers(pgp=["KEY_123"], wallets=["W_123"]),
        stylometry=Stylometry(document_count=10, avg_sentence_length=15.0, punctuation_rate=3.0),
        activity=Activity(posting_hours=[1, 2, 3]),
        infrastructure=Infrastructure(tls_fingerprints=["TLS_123"]),
    )
    b = ActorProfile(
        actor_id="ACTOR_B",
        identifiers=Identifiers(pgp=["KEY_123"], wallets=["W_123"]),
        stylometry=Stylometry(document_count=10, avg_sentence_length=15.2, punctuation_rate=3.1),
        activity=Activity(posting_hours=[1, 2, 4]),
        infrastructure=Infrastructure(tls_fingerprints=["TLS_123"]),
    )
    return a, b

def test_weighted_scorer_matching_pair(test_pair):
    a, b = test_pair
    scorer = WeightedScorer()
    res = scorer.evaluate_pair(a, b)

    assert res.decision == "SUPPORTED_CORRELATION"
    assert res.correlation_index >= 70.0
    assert res.evidence_coverage == 1.0
    assert res.risk.level == "UNKNOWN"
    assert res.risk.status == "INSUFFICIENT_THREAT_FACTS"

def test_separate_risk_assessment():
    risk_default = RiskAssessor.assess_risk(None)
    assert risk_default.level == "UNKNOWN"

    threat_facts = [
        {"category": "Exploit Broker", "severity": "HIGH"},
        {"category": "Ransomware Operator", "severity": "HIGH"},
    ]
    risk_assessed = RiskAssessor.assess_risk(threat_facts)
    assert risk_assessed.level == "HIGH"
    assert risk_assessed.status == "SUPPORTED_THREAT_FACTS"

