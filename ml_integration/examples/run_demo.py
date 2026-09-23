import os
import json
from features.profile_builder import ProfileBuilder
from scoring.weighted_scorer import WeightedScorer
from scoring.counterfactual import CounterfactualEngine
from api.agent_tools import CorrelationAgentTools
from evaluation.run_evaluation import LeakageControlledEvaluator
from examples.generate_sample_dataset import generate_sample_csv

def main():
    print("=" * 70)
    print(" PERSON 4 — ML, CORRELATION & EXPLAINABILITY ENGINE DEMO")
    print("=" * 70)

    # 1. Generate sample dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "sample_master_dataset.csv")
    df = generate_sample_csv(dataset_path, num_rows=200, num_users=20)

    # 2. Build Actor Profiles
    profiles = ProfileBuilder.build_profiles_from_df(df)
    print(f"\nExtracted {len(profiles)} standardized Actor Profiles.")

    # Select two profiles for correlation comparison
    actor_a = profiles["USER_100"]
    actor_b = profiles["USER_101"]

    print(f"\nComparing Actor A ({actor_a.actor_id}) vs Actor B ({actor_b.actor_id}):")
    print(f"  Actor A PGP: {actor_a.identifiers.pgp}")
    print(f"  Actor B PGP: {actor_b.identifiers.pgp}")
    print(f"  Actor A Wallets: {actor_a.identifiers.wallets}")
    print(f"  Actor B Wallets: {actor_b.identifiers.wallets}")

    # 3. Evaluate Pair using Scorer
    scorer = WeightedScorer()
    threat_facts = [{"category": "Ransomware Operations", "severity": "HIGH"}]
    result = scorer.evaluate_pair(actor_a, actor_b, threat_facts=threat_facts)

    print("\n--- Baseline Correlation Result ---")
    print(json.dumps(result.to_dict(), indent=2))

    # 4. Counterfactual Recalculation (Live Evidence Toggle)
    print("\n--- Counterfactual Recalculation (Removing PGP evidence) ---")
    counterfactual = CounterfactualEngine.recalculate_without(result, exclude_target="PGP")
    print(json.dumps(counterfactual.to_dict(), indent=2))

    # 5. Agent Tools Demonstration
    print("\n--- Agent Tool Invocation (calculate_correlation) ---")
    tools = CorrelationAgentTools(scorer)
    tool_out = tools.calculate_correlation(actor_a.to_dict(), actor_b.to_dict())
    print(f"Correlation Index: {tool_out['correlation_index']} | Decision: {tool_out['decision']}")

    # 6. Evaluation Harness Demonstration
    print("\n--- Running Leakage-Controlled Day 4 Evaluation ---")
    evaluator = LeakageControlledEvaluator(scorer)
    pos_pairs = [(profiles["USER_100"], profiles["USER_101"])]
    neg_pairs = [(profiles["USER_100"], profiles["USER_105"])]

    eval_metrics = evaluator.evaluate(pos_pairs, neg_pairs, mask_deterministic=True)
    print(json.dumps(eval_metrics.to_dict(), indent=2))

    print("\n[SUCCESS] Demo completed smoothly.")

if __name__ == "__main__":
    main()
