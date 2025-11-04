"""
Tests for ScoringEngine.
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scenarios.security.scoring_engine import ScoringEngine
from scenarios.security.models import TestResult, DetectionOutcome, ConfusionMatrix


class TestScoringEngine:
    """Test suite for ScoringEngine."""

    @pytest.fixture
    def engine(self):
        """Fixture providing ScoringEngine instance."""
        return ScoringEngine()

    @pytest.fixture
    def perfect_results(self):
        """Fixture providing perfect detection results."""
        return [
            TestResult(
                test_case_id="1",
                ground_truth=True,
                predicted=True,
                outcome=DetectionOutcome.TRUE_POSITIVE,
                category="classic_sqli",
                language="python",
                confidence=0.9
            ),
            TestResult(
                test_case_id="2",
                ground_truth=True,
                predicted=True,
                outcome=DetectionOutcome.TRUE_POSITIVE,
                category="classic_sqli",
                language="python",
                confidence=0.95
            ),
            TestResult(
                test_case_id="3",
                ground_truth=False,
                predicted=False,
                outcome=DetectionOutcome.TRUE_NEGATIVE,
                category="classic_sqli",
                language="python",
                confidence=0.8
            ),
            TestResult(
                test_case_id="4",
                ground_truth=False,
                predicted=False,
                outcome=DetectionOutcome.TRUE_NEGATIVE,
                category="classic_sqli",
                language="python",
                confidence=0.85
            ),
        ]

    @pytest.fixture
    def mixed_results(self):
        """Fixture providing mixed detection results."""
        return [
            # True Positives
            TestResult(
                test_case_id="1",
                ground_truth=True,
                predicted=True,
                outcome=DetectionOutcome.TRUE_POSITIVE,
                category="classic_sqli",
                language="python",
                confidence=0.9
            ),
            TestResult(
                test_case_id="2",
                ground_truth=True,
                predicted=True,
                outcome=DetectionOutcome.TRUE_POSITIVE,
                category="blind_sqli",
                language="python",
                confidence=0.85
            ),
            # True Negatives
            TestResult(
                test_case_id="3",
                ground_truth=False,
                predicted=False,
                outcome=DetectionOutcome.TRUE_NEGATIVE,
                category="classic_sqli",
                language="python",
                confidence=0.8
            ),
            # False Positives
            TestResult(
                test_case_id="4",
                ground_truth=False,
                predicted=True,
                outcome=DetectionOutcome.FALSE_POSITIVE,
                category="classic_sqli",
                language="python",
                confidence=0.7
            ),
            # False Negatives
            TestResult(
                test_case_id="5",
                ground_truth=True,
                predicted=False,
                outcome=DetectionOutcome.FALSE_NEGATIVE,
                category="blind_sqli",
                language="python",
                confidence=0.3
            ),
        ]

    def test_calculate_metrics_perfect(self, engine, perfect_results):
        """Test metrics calculation with perfect results."""
        metrics = engine.calculate_metrics(perfect_results)

        assert metrics.f1_score == 1.0
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.accuracy == 1.0
        assert metrics.false_positive_rate == 0.0
        assert metrics.false_negative_rate == 0.0

        print(f"\n✓ Perfect detection:")
        print(f"  - F1: {metrics.f1_score:.3f}")
        print(f"  - Precision: {metrics.precision:.3f}")
        print(f"  - Recall: {metrics.recall:.3f}")

    def test_calculate_metrics_mixed(self, engine, mixed_results):
        """Test metrics calculation with mixed results."""
        metrics = engine.calculate_metrics(mixed_results)

        # TP=2, TN=1, FP=1, FN=1
        assert metrics.confusion_matrix.true_positives == 2
        assert metrics.confusion_matrix.true_negatives == 1
        assert metrics.confusion_matrix.false_positives == 1
        assert metrics.confusion_matrix.false_negatives == 1

        # Precision = TP / (TP + FP) = 2 / 3 = 0.667
        assert abs(metrics.precision - 0.667) < 0.01

        # Recall = TP / (TP + FN) = 2 / 3 = 0.667
        assert abs(metrics.recall - 0.667) < 0.01

        # F1 = 2 * (P * R) / (P + R) = 2 * (0.667 * 0.667) / 1.334 = 0.667
        assert abs(metrics.f1_score - 0.667) < 0.01

        print(f"\n✓ Mixed detection:")
        print(f"  - F1: {metrics.f1_score:.3f}")
        print(f"  - Precision: {metrics.precision:.3f}")
        print(f"  - Recall: {metrics.recall:.3f}")
        print(f"  - Confusion: TP={metrics.confusion_matrix.true_positives}, "
              f"TN={metrics.confusion_matrix.true_negatives}, "
              f"FP={metrics.confusion_matrix.false_positives}, "
              f"FN={metrics.confusion_matrix.false_negatives}")

    def test_calculate_category_metrics(self, engine, mixed_results):
        """Test per-category metrics calculation."""
        category_metrics = engine.calculate_category_metrics(mixed_results)

        assert len(category_metrics) == 2  # classic_sqli and blind_sqli

        # Find classic_sqli metrics
        classic = next(cm for cm in category_metrics if cm.category == "classic_sqli")
        assert classic.sample_count == 3

        # Find blind_sqli metrics
        blind = next(cm for cm in category_metrics if cm.category == "blind_sqli")
        assert blind.sample_count == 2

        print(f"\n✓ Category metrics:")
        for cm in category_metrics:
            print(f"  - {cm.category}: F1={cm.metrics.f1_score:.3f}, samples={cm.sample_count}")

    def test_get_weak_categories(self, engine):
        """Test weak category identification."""
        from scenarios.security.models import CategoryMetrics, EvaluationMetrics, ConfusionMatrix

        category_metrics = [
            CategoryMetrics(
                category="classic_sqli",
                metrics=EvaluationMetrics(
                    f1_score=0.9,
                    precision=0.9,
                    recall=0.9,
                    specificity=0.9,
                    accuracy=0.9,
                    false_positive_rate=0.1,
                    false_negative_rate=0.1,
                    confusion_matrix=ConfusionMatrix(true_positives=9, true_negatives=9, false_positives=1, false_negatives=1),
                    total_samples=20
                ),
                sample_count=20
            ),
            CategoryMetrics(
                category="blind_sqli",
                metrics=EvaluationMetrics(
                    f1_score=0.5,
                    precision=0.5,
                    recall=0.5,
                    specificity=0.5,
                    accuracy=0.5,
                    false_positive_rate=0.5,
                    false_negative_rate=0.5,
                    confusion_matrix=ConfusionMatrix(true_positives=5, true_negatives=5, false_positives=5, false_negatives=5),
                    total_samples=20
                ),
                sample_count=20
            )
        ]

        weak = engine.get_weak_categories(category_metrics, threshold=0.6)
        strong = engine.get_strong_categories(category_metrics, threshold=0.6)

        assert "blind_sqli" in weak
        assert "classic_sqli" in strong

        print(f"\n✓ Category strength:")
        print(f"  - Strong: {strong}")
        print(f"  - Weak: {weak}")

    def test_compare_metrics(self, engine, mixed_results, perfect_results):
        """Test metrics comparison."""
        metrics1 = engine.calculate_metrics(mixed_results)
        metrics2 = engine.calculate_metrics(perfect_results)

        comparison = engine.compare_metrics(metrics1, metrics2)

        assert comparison["f1_change"] > 0  # Improved
        assert comparison["precision_change"] > 0
        assert comparison["recall_change"] > 0

        print(f"\n✓ Metrics comparison:")
        print(f"  - F1 change: {comparison['f1_change']:+.3f}")
        print(f"  - Precision change: {comparison['precision_change']:+.3f}")
        print(f"  - Recall change: {comparison['recall_change']:+.3f}")

    def test_is_performance_stable(self, engine, perfect_results):
        """Test performance stability detection."""
        metrics1 = engine.calculate_metrics(perfect_results)
        metrics2 = engine.calculate_metrics(perfect_results)  # Same metrics

        is_stable = engine.is_performance_stable(metrics1, metrics2, threshold=0.05)
        assert is_stable

        print(f"\n✓ Performance stability check: {'Stable' if is_stable else 'Unstable'}")

    def test_analyze_confidence_distribution(self, engine, mixed_results):
        """Test confidence distribution analysis."""
        analysis = engine.analyze_confidence_distribution(mixed_results)

        assert "overall" in analysis
        assert "correct_predictions" in analysis
        assert "incorrect_predictions" in analysis

        assert analysis["total_results"] == len(mixed_results)
        assert analysis["correct_count"] + analysis["incorrect_count"] == len(mixed_results)

        print(f"\n✓ Confidence analysis:")
        print(f"  - Overall mean: {analysis['overall']['mean']:.3f}")
        print(f"  - Correct mean: {analysis['correct_predictions']['mean']:.3f}")
        print(f"  - Incorrect mean: {analysis['incorrect_predictions']['mean']:.3f}")

    def test_generate_summary_report(self, engine, mixed_results):
        """Test summary report generation."""
        overall_metrics = engine.calculate_metrics(mixed_results)
        category_metrics = engine.calculate_category_metrics(mixed_results)

        report = engine.generate_summary_report(overall_metrics, category_metrics)

        assert "overall_performance" in report
        assert "confusion_matrix" in report
        assert "category_analysis" in report
        assert "category_scores" in report

        print(f"\n✓ Summary report generated:")
        print(f"  - F1 Score: {report['overall_performance']['f1_score']:.3f}")
        print(f"  - Categories: {report['category_analysis']['total_categories']}")
        print(f"  - Best: {report['category_analysis']['best_category']}")
        print(f"  - Worst: {report['category_analysis']['worst_category']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
