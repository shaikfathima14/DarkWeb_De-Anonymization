import pytest
from fastapi.testclient import TestClient
from api.fastapi_app import app
from models.actor_profile import ActorProfile, Identifiers, Stylometry

client = TestClient(app)

def test_fastapi_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_fastapi_compare_endpoint():
    a = ActorProfile(
        actor_id="ACTOR_A",
        identifiers=Identifiers(pgp=["KEY_123"]),
        stylometry=Stylometry(document_count=5, avg_sentence_length=12.0),
    ).to_dict()

    b = ActorProfile(
        actor_id="ACTOR_B",
        identifiers=Identifiers(pgp=["KEY_123"]),
        stylometry=Stylometry(document_count=5, avg_sentence_length=12.5),
    ).to_dict()

    payload = {
        "actor_a": a,
        "actor_b": b,
        "threat_facts": None,
    }

    response = client.post("/api/correlation/compare", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "correlation_index" in res_data
    assert res_data["actor_a"] == "ACTOR_A"

def test_fastapi_recalculate_endpoint():
    a = ActorProfile(
        actor_id="ACTOR_A",
        identifiers=Identifiers(pgp=["KEY_123"]),
        stylometry=Stylometry(document_count=5, avg_sentence_length=12.0),
    ).to_dict()

    b = ActorProfile(
        actor_id="ACTOR_B",
        identifiers=Identifiers(pgp=["KEY_123"]),
        stylometry=Stylometry(document_count=5, avg_sentence_length=12.5),
    ).to_dict()

    compare_res = client.post("/api/correlation/compare", json={"actor_a": a, "actor_b": b}).json()

    recalc_payload = {
        "investigation_result": compare_res,
        "exclude_target": "PGP",
    }

    response = client.post("/api/correlation/recalculate", json=recalc_payload)
    assert response.status_code == 200
    recalc_data = response.json()
    assert "counterfactual_score" in recalc_data
    assert recalc_data["difference"] >= 0.0
