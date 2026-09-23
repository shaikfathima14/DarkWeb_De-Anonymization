from typing import Dict, Any, List, Optional
from models.actor_profile import ActorProfile
from scoring.weighted_scorer import WeightedScorer
from scoring.counterfactual import CounterfactualEngine

class CorrelationAgentTools:
    """
    Agent-callable tool interfaces matching Person 2's Orchestrator tool schemas.
    Follows rule: Python engine calculates; agent/LLM explains.
    """

    def __init__(self, scorer: Optional[WeightedScorer] = None):
        self.scorer = scorer or WeightedScorer()

    def calculate_correlation(
        self,
        actor_a_dict: Dict[str, Any],
        actor_b_dict: Dict[str, Any],
        threat_facts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tool: calculate_correlation
        Input: actor_a profile dict, actor_b profile dict, optional threat facts
        Output: Structured correlation result payload
        """
        profile_a = self._dict_to_profile(actor_a_dict)
        profile_b = self._dict_to_profile(actor_b_dict)

        result = self.scorer.evaluate_pair(profile_a, profile_b, threat_facts=threat_facts)
        return result.to_dict()

    def recalculate_without(
        self,
        investigation_result_dict: Dict[str, Any],
        exclude_target: Any
    ) -> Dict[str, Any]:
        """
        Tool: recalculate_without
        Input: previous investigation result dict, evidence_id or evidence_type to exclude
        Output: Counterfactual recalculation payload with score difference and changed decision
        """
        # Reconstruct result object
        actor_a = investigation_result_dict.get("actor_a", "ACTOR_A")
        actor_b = investigation_result_dict.get("actor_b", "ACTOR_B")
        
        # We can construct a lightweight CorrelationResult from the dictionary
        from models.result import CorrelationResult, ThreatRisk
        from models.evidence import Evidence

        ev_list = []
        for e in investigation_result_dict.get("evidence", []):
            ev_list.append(Evidence(
                evidence_id=e.get("evidence_id", ""),
                type=e.get("type", ""),
                status=e.get("status", "UNKNOWN"),
                similarity=float(e.get("similarity", 0.0)),
                quality=float(e.get("quality", 0.0)),
                actor_a=actor_a,
                actor_b=actor_b,
                sources=e.get("sources", []),
                independent=bool(e.get("independent", True)),
                explanation=e.get("explanation", ""),
                contribution=float(e.get("contribution", 0.0))
            ))

        res = CorrelationResult(
            actor_a=actor_a,
            actor_b=actor_b,
            correlation_index=float(investigation_result_dict.get("correlation_index", 0.0)),
            decision=investigation_result_dict.get("decision", "LOW_CORRELATION"),
            evidence_coverage=float(investigation_result_dict.get("evidence_coverage", 0.0)),
            evidence=ev_list,
            limitations=investigation_result_dict.get("limitations", []),
            scoring_version=investigation_result_dict.get("scoring_version", "1.0"),
        )

        counterfactual_res = CounterfactualEngine.recalculate_without(res, exclude_target)
        return counterfactual_res.to_dict()

    @staticmethod
    def _dict_to_profile(d: Dict[str, Any]) -> ActorProfile:
        from models.actor_profile import ActorProfile, Identifiers, Stylometry, Activity, Infrastructure

        id_dict = d.get("identifiers", {})
        identifiers = Identifiers(
            pgp=id_dict.get("pgp", []),
            wallets=id_dict.get("wallets", []),
            emails=id_dict.get("emails", []),
            aliases=id_dict.get("aliases", []),
        )

        sty_dict = d.get("stylometry", {})
        stylometry = Stylometry(
            language=sty_dict.get("language", "en"),
            document_count=int(sty_dict.get("document_count", 0)),
            avg_sentence_length=sty_dict.get("avg_sentence_length"),
            vocabulary_diversity=sty_dict.get("vocabulary_diversity"),
            punctuation_rate=sty_dict.get("punctuation_rate"),
            function_word_frequency=sty_dict.get("function_word_frequency", {}),
            phrase_features=sty_dict.get("phrase_features", {}),
        )

        act_dict = d.get("activity", {})
        activity = Activity(
            posting_hours=act_dict.get("posting_hours", []),
            weekday_distribution=act_dict.get("weekday_distribution", {}),
            activity_frequency=act_dict.get("activity_frequency", {}),
        )

        inf_dict = d.get("infrastructure", {})
        infrastructure = Infrastructure(
            tls_fingerprints=inf_dict.get("tls_fingerprints", []),
            sanitized_network_fingerprints=inf_dict.get("sanitized_network_fingerprints", []),
            hosting_identifiers=inf_dict.get("hosting_identifiers", []),
        )

        return ActorProfile(
            actor_id=str(d.get("actor_id", "ACTOR_UNKNOWN")),
            profile_version=str(d.get("profile_version", "1.0")),
            identifiers=identifiers,
            stylometry=stylometry,
            activity=activity,
            infrastructure=infrastructure,
            sources=d.get("sources", []),
        )
