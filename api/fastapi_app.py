from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from api.agent_tools import CorrelationAgentTools

app = FastAPI(
    title="Person 4 — ML / Correlation & Explainability Engine API",
    description="SIH26151 Dark Web Threat Actor De-anonymization System",
    version="1.0.0"
)

agent_tools = CorrelationAgentTools()

class CompareRequest(BaseModel):
    actor_a: Dict[str, Any]
    actor_b: Dict[str, Any]
    threat_facts: Optional[List[Dict[str, Any]]] = None

class RecalculateRequest(BaseModel):
    investigation_result: Dict[str, Any]
    exclude_target: Any

@app.get("/")
def health_check():
    return {"status": "ok", "service": "ML Correlation Engine", "version": "1.0.0"}

@app.post("/api/correlation/compare")
def compare_profiles(req: CompareRequest):
    try:
        result = agent_tools.calculate_correlation(req.actor_a, req.actor_b, req.threat_facts)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/correlation/recalculate")
def recalculate_without(req: RecalculateRequest):
    try:
        result = agent_tools.recalculate_without(req.investigation_result, req.exclude_target)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
