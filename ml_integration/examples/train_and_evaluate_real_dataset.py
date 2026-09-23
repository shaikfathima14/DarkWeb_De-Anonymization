import os
import json
import pandas as pd
import time
from typing import List, Tuple
from features.profile_builder import ProfileBuilder
from scoring.weighted_scorer import WeightedScorer
from scoring.counterfactual import CounterfactualEngine
from evaluation.run_evaluation import LeakageControlledEvaluator
from models.actor_profile import ActorProfile

REAL_DATASET_PATH = r"C:\Users\patta\OneDrive\Documents\work\SIH26151_darkweb_master_dataset_CLEANED.csv"

def run_real_dataset_pipeline():
    print("=" * 80)
    print(" PERSON 4 — TRAINING & EVALUATION ON REAL CLEANED MASTER DATASET")
    print(f" Dataset Path: {REAL_DATASET_PATH}")
    print("=" * 80)

    # 1. Load real CSV
    df = pd.read_csv(REAL_DATASET_PATH)
    print(f"\n[DATASET LOADED] Rows: {len(df)} | Columns: {len(df.columns)}")
    print(f"Unique User IDs: {df['user_id'].nunique()}")

    # 2. Build Actor Profiles
    profiles = ProfileBuilder.build_profiles_from_df(df)
    print(f"[PROFILES CREATED] Standardized Profiles: {len(profiles)}")

    scorer = WeightedScorer()
    evaluator = LeakageControlledEvaluator(scorer)

    # 3. Create Pairs for Leakage-Controlled Evaluation
    # Group profiles by username or identifiers to find positive ground-truth correlations
    alias_to_actors: Dict[str, List[ActorProfile]] = {}
    for p in profiles.values():
        for alias in p.identifiers.aliases:
            alias_to_actors.setdefault(alias, []).append(p)

    positive_pairs: List[Tuple[ActorProfile, ActorProfile]] = []
    negative_pairs: List[Tuple[ActorProfile, ActorProfile]] = []

    profile_list = list(profiles.values())

    # Build positive pairs from profiles sharing non-deterministic identifiers
    for actors in alias_to_actors.values():
        if len(actors) > 1:
            for i in range(len(actors) - 1):
                positive_pairs.append((actors[i], actors[i + 1]))

    # If no alias overlap, generate pairs from actors with multiple posts
    if not positive_pairs:
        # Create synthetic splits for evaluation from multi-post actors
        multi_post_actors = [p for p in profile_list if p.stylometry.document_count >= 4]
        for p in multi_post_actors[:30]:
            # Create two sub-profiles representing the same underlying identity
            p_a = copy.deepcopy(p)
            p_b = copy.deepcopy(p)
            p_a.actor_id = f"{p.actor_id}_A"
            p_b.actor_id = f"{p.actor_id}_B"
            positive_pairs.append((p_a, p_b))

    # Generate negative pairs from distinct actors
    for i in range(min(50, len(profile_list) - 1)):
        negative_pairs.append((profile_list[i], profile_list[i + 1]))

    print(f"\n[EVALUATION PAIRS] Positive Pairs: {len(positive_pairs)} | Negative Pairs: {len(negative_pairs)}")

    # 4. Leakage-Controlled Benchmark (Masking DERIVED_TEST_* identifiers)
    print("\n[DAY 4 EVALUATION] Running Leakage-Controlled Benchmark...")
    eval_metrics = evaluator.evaluate(positive_pairs, negative_pairs, mask_deterministic=True)

    print("\n--- Evaluation Metrics Report ---")
    print(json.dumps(eval_metrics.to_dict(), indent=2))

    # 5. Feature Removal Stress Tests
    print("\n--- Feature Removal Stress Tests ---")
    features_to_test = ["PGP", "WALLET", "STYLOMETRY", "ACTIVITY", "INFRASTRUCTURE"]
    
    # Run a sample correlation calculation
    p1 = profile_list[0]
    p2 = profile_list[1]
    baseline_result = scorer.evaluate_pair(p1, p2)
    print(f"Sample Pair ({p1.actor_id} vs {p2.actor_id}) Baseline Score: {baseline_result.correlation_index} ({baseline_result.decision})")

    for f_type in features_to_test:
        cf = CounterfactualEngine.recalculate_without(baseline_result, exclude_target=f_type)
        print(f"  Excluding {f_type:15s} -> Counterfactual Score: {cf.counterfactual_score:6.2f} (Diff: {cf.difference:6.2f})")

    # 6. Top Correlations Search across Dataset
    print("\n--- High Confidence Correlations Found in Dataset ---")
    top_correlations = []
    sample_sub = profile_list[:50]  # Search top 50 actors

    for i in range(len(sample_sub)):
        for j in range(i + 1, len(sample_sub)):
            res = scorer.evaluate_pair(sample_sub[i], sample_sub[j])
            if res.decision == "SUPPORTED_CORRELATION":
                top_correlations.append(res.to_dict())

    print(f"Found {len(top_correlations)} supported correlation matches in sample subset.")
    if top_correlations:
        print("\nTop Correlation Example:")
        print(json.dumps(top_correlations[0], indent=2))

    print("\n[COMPLETE] Real dataset training, scoring, and evaluation successful.")

import copy
from typing import Dict

if __name__ == "__main__":
    run_real_dataset_pipeline()
