import pytest
from models.actor_profile import ActorProfile, Identifiers, Stylometry, Activity, Infrastructure
from features.identifier_features import IdentifierComparator
from features.stylometric_features import StylometryComparator
from features.activity_features import ActivityComparator
from features.infrastructure_features import InfrastructureComparator

@pytest.fixture
def sample_profiles():
    profile_a = ActorProfile(
        actor_id="ACTOR_001",
        identifiers=Identifiers(
            pgp=["4A92F001B1C88D"],
            wallets=["bc1qxy001z89q23"],
            emails=["actor1@onionmail.org"],
            aliases=["shadow_hacker"],
        ),
        stylometry=Stylometry(
            language="en",
            document_count=10,
            avg_sentence_length=15.5,
            vocabulary_diversity=0.45,
            punctuation_rate=4.2,
        ),
        activity=Activity(
            posting_hours=[2, 3, 4, 14, 15, 16],
        ),
        infrastructure=Infrastructure(
            tls_fingerprints=["tls_fp_001"],
            sanitized_network_fingerprints=["darkmarket1.onion"],
        ),
        sources=["SRC-001"],
    )

    profile_b = ActorProfile(
        actor_id="ACTOR_002",
        identifiers=Identifiers(
            pgp=["4A92F001B1C88D"],  # Matching PGP key
            wallets=["bc1qxy999z89q99"],  # Different Wallet
            emails=["actor2@onionmail.org"],
            aliases=["night_runner"],
        ),
        stylometry=Stylometry(
            language="en",
            document_count=8,
            avg_sentence_length=16.0,
            vocabulary_diversity=0.42,
            punctuation_rate=4.0,
        ),
        activity=Activity(
            posting_hours=[2, 3, 5, 14, 15, 17],
        ),
        infrastructure=Infrastructure(
            tls_fingerprints=["tls_fp_001"],
        ),
        sources=["SRC-002"],
    )

    profile_sparse = ActorProfile(
        actor_id="ACTOR_SPARSE",
        stylometry=Stylometry(document_count=1),
    )

    return profile_a, profile_b, profile_sparse

def test_pgp_comparator_match(sample_profiles):
    a, b, _ = sample_profiles
    ev = IdentifierComparator.compare_pgp(a, b)
    assert ev.status == "MATCH"
    assert ev.similarity == 1.0
    assert ev.type == "PGP"

def test_pgp_comparator_unknown(sample_profiles):
    a, _, sparse = sample_profiles
    ev = IdentifierComparator.compare_pgp(a, sparse)
    assert ev.status == "UNKNOWN"
    assert ev.similarity == 0.0

def test_wallet_comparator_no_match(sample_profiles):
    a, b, _ = sample_profiles
    ev = IdentifierComparator.compare_wallets(a, b)
    assert ev.status == "NO_MATCH"
    assert ev.similarity == 0.0

def test_stylometry_insufficient_data(sample_profiles):
    a, _, sparse = sample_profiles
    ev = StylometryComparator.compare_stylometry(a, sparse)
    assert ev.status == "INSUFFICIENT_DATA"

def test_stylometry_match(sample_profiles):
    a, b, _ = sample_profiles
    ev = StylometryComparator.compare_stylometry(a, b)
    assert ev.status == "MATCH"
    assert ev.similarity > 0.80

def test_activity_comparator(sample_profiles):
    a, b, _ = sample_profiles
    ev = ActivityComparator.compare_activity(a, b)
    assert ev.status in ("MATCH", "PARTIAL_MATCH")
    assert ev.similarity > 0.50

def test_infrastructure_comparator(sample_profiles):
    a, b, _ = sample_profiles
    ev = InfrastructureComparator.compare_infrastructure(a, b)
    assert ev.status == "MATCH"
    assert ev.similarity == 1.0
