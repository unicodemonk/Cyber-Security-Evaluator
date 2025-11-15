"""
Simple script to test the evaluation system locally.

This simulates what would happen when the Green Agent evaluates the Purple Agent.
"""

import asyncio
import httpx
from scenarios.security.models import CodeSample, PurpleAgentResponse, DetectionOutcome, TestResult
from scenarios.security.dataset_manager import DatasetManager
from framework.scoring import GreenAgentScoringEngine

async def test_purple_agent():
    """Test the Purple Agent with a few samples and show results."""

    print("=" * 70)
    print("🧪 SQL Injection Detection - Evaluation Test")
    print("=" * 70)
    print()

    # Initialize components
    dataset_manager = DatasetManager("datasets/sql_injection")
    dataset_manager.load_datasets()
    scoring_engine = GreenAgentScoringEngine()

    # Get some test samples
    print("📋 Loading test samples...")
    test_samples = dataset_manager.sample_diverse(n=10, seed=42)
    print(f"   Selected {len(test_samples)} diverse samples\n")

    # Call Purple Agent for each sample
    results = []
    purple_agent_url = "http://127.0.0.1:8000/detect"

    print("🔍 Testing Purple Agent...")
    print("-" * 70)

    async with httpx.AsyncClient(timeout=10.0) as client:
        for i, sample in enumerate(test_samples, 1):
            try:
                # Call Purple Agent
                request_data = {
                    "test_case_id": sample.id,
                    "code": sample.code,
                    "language": sample.language,
                    "category": sample.category
                }

                response = await client.post(purple_agent_url, json=request_data)
                response.raise_for_status()
                purple_response = response.json()

                # Determine outcome
                ground_truth = sample.is_vulnerable
                predicted = purple_response["is_vulnerable"]

                if ground_truth and predicted:
                    outcome = DetectionOutcome.TRUE_POSITIVE
                    result_emoji = "✅ TP"
                elif not ground_truth and not predicted:
                    outcome = DetectionOutcome.TRUE_NEGATIVE
                    result_emoji = "✅ TN"
                elif not ground_truth and predicted:
                    outcome = DetectionOutcome.FALSE_POSITIVE
                    result_emoji = "❌ FP"
                else:
                    outcome = DetectionOutcome.FALSE_NEGATIVE
                    result_emoji = "❌ FN"

                # Create test result
                result = TestResult(
                    test_case_id=sample.id,
                    ground_truth=ground_truth,
                    predicted=predicted,
                    outcome=outcome,
                    category=sample.category,
                    language=sample.language,
                    confidence=purple_response.get("confidence", 0.5)
                )
                results.append(result)

                # Print result
                vuln_status = "VULNERABLE" if ground_truth else "SECURE    "
                pred_status = "VULNERABLE" if predicted else "SECURE    "
                confidence = purple_response.get("confidence", 0.5)

                print(f"{i:2d}. {result_emoji} | Truth: {vuln_status} | Predicted: {pred_status} | "
                      f"Confidence: {confidence:.2f} | {sample.category[:15]:15s}")

            except Exception as e:
                print(f"{i:2d}. ⚠️  ERROR: {e}")

    print("-" * 70)
    print()

    # Calculate metrics
    if results:
        metrics = scoring_engine.calculate_metrics(results)
        category_metrics = scoring_engine.calculate_category_metrics(results)

        print("📊 EVALUATION RESULTS")
        print("=" * 70)
        print()

        # Overall metrics
        print("Overall Performance:")
        print(f"  • F1 Score:          {metrics.f1_score:.3f}")
        print(f"  • Precision:         {metrics.precision:.3f}")
        print(f"  • Recall:            {metrics.recall:.3f}")
        print(f"  • Accuracy:          {metrics.accuracy:.3f}")
        print()

        # Confusion Matrix
        print("Confusion Matrix:")
        print(f"  • True Positives:    {metrics.confusion_matrix.true_positives}")
        print(f"  • True Negatives:    {metrics.confusion_matrix.true_negatives}")
        print(f"  • False Positives:   {metrics.confusion_matrix.false_positives}")
        print(f"  • False Negatives:   {metrics.confusion_matrix.false_negatives}")
        print()

        # Error rates
        print("Error Rates:")
        print(f"  • False Positive Rate: {metrics.false_positive_rate:.3f}")
        print(f"  • False Negative Rate: {metrics.false_negative_rate:.3f}")
        print()

        # Per-category breakdown
        if category_metrics:
            print("Per-Category Performance:")
            for cat_metric in category_metrics:
                print(f"  • {cat_metric.category:20s} | F1: {cat_metric.metrics.f1_score:.3f} | "
                      f"Samples: {cat_metric.sample_count}")
            print()

        # Identify weak areas
        weak_categories = scoring_engine.get_weak_categories(category_metrics, threshold=0.6)
        if weak_categories:
            print("🎯 Weak Categories (F1 < 0.6):")
            for cat in weak_categories:
                print(f"  • {cat}")
            print("\n  👉 In adaptive mode, the system would focus 60% of tests on these areas!")
        else:
            print("✨ All categories performing well (F1 >= 0.6)")

        print()
        print("=" * 70)
        print("✅ Evaluation Complete!")
        print("=" * 70)


if __name__ == "__main__":
    print("\n🚀 Starting evaluation test...")
    print("   Make sure Purple Agent is running on http://127.0.0.1:8000\n")
    asyncio.run(test_purple_agent())
