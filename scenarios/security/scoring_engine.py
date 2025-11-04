"""
Scoring Engine for SQL Injection Detection Benchmark.

This module calculates comprehensive evaluation metrics including:
- Confusion matrix (TP, TN, FP, FN)
- F1 score, Precision, Recall
- Specificity, Accuracy
- False Positive Rate, False Negative Rate
- Per-category metrics
"""

from typing import Any
from collections import defaultdict

from .models import (
    TestResult,
    DetectionOutcome,
    ConfusionMatrix,
    EvaluationMetrics,
    CategoryMetrics
)


class ScoringEngine:
    """
    Calculates evaluation metrics for security detection performance.

    Provides both overall metrics and per-category breakdowns to identify
    strengths and weaknesses in purple agent detection capabilities.
    """

    def __init__(self):
        """Initialize the scoring engine."""
        pass

    def calculate_metrics(self, results: list[TestResult]) -> EvaluationMetrics:
        """
        Calculate comprehensive evaluation metrics from test results.

        Args:
            results: List of test results to evaluate

        Returns:
            EvaluationMetrics with all calculated scores

        Raises:
            ValueError: If results list is empty
        """
        if not results:
            raise ValueError("Cannot calculate metrics from empty results list")

        # Count outcomes
        confusion = self._build_confusion_matrix(results)

        # Calculate derived metrics
        precision = self._calculate_precision(confusion)
        recall = self._calculate_recall(confusion)
        f1 = self._calculate_f1(precision, recall)
        specificity = self._calculate_specificity(confusion)
        accuracy = self._calculate_accuracy(confusion)
        fpr = self._calculate_fpr(confusion)
        fnr = self._calculate_fnr(confusion)

        return EvaluationMetrics(
            f1_score=f1,
            precision=precision,
            recall=recall,
            specificity=specificity,
            accuracy=accuracy,
            false_positive_rate=fpr,
            false_negative_rate=fnr,
            confusion_matrix=confusion,
            total_samples=confusion.total
        )

    def calculate_category_metrics(
        self,
        results: list[TestResult]
    ) -> list[CategoryMetrics]:
        """
        Calculate metrics for each category separately.

        Args:
            results: List of test results

        Returns:
            List of CategoryMetrics, one per category
        """
        # Group results by category
        results_by_category = defaultdict(list)
        for result in results:
            results_by_category[result.category].append(result)

        # Calculate metrics for each category
        category_metrics = []
        for category, cat_results in results_by_category.items():
            metrics = self.calculate_metrics(cat_results)
            category_metrics.append(
                CategoryMetrics(
                    category=category,
                    metrics=metrics,
                    sample_count=len(cat_results)
                )
            )

        # Sort by category name for consistency
        category_metrics.sort(key=lambda x: x.category)

        return category_metrics

    def _build_confusion_matrix(self, results: list[TestResult]) -> ConfusionMatrix:
        """
        Build confusion matrix from test results.

        Args:
            results: List of test results

        Returns:
            ConfusionMatrix with counts
        """
        tp = sum(1 for r in results if r.outcome == DetectionOutcome.TRUE_POSITIVE)
        tn = sum(1 for r in results if r.outcome == DetectionOutcome.TRUE_NEGATIVE)
        fp = sum(1 for r in results if r.outcome == DetectionOutcome.FALSE_POSITIVE)
        fn = sum(1 for r in results if r.outcome == DetectionOutcome.FALSE_NEGATIVE)

        return ConfusionMatrix(
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn
        )

    def _calculate_precision(self, confusion: ConfusionMatrix) -> float:
        """
        Calculate Precision = TP / (TP + FP).

        Precision measures how many of the detections were actually vulnerable.
        High precision = few false alarms.

        Args:
            confusion: Confusion matrix

        Returns:
            Precision score (0.0 to 1.0)
        """
        denominator = confusion.true_positives + confusion.false_positives
        if denominator == 0:
            return 0.0
        return confusion.true_positives / denominator

    def _calculate_recall(self, confusion: ConfusionMatrix) -> float:
        """
        Calculate Recall (TPR, Sensitivity) = TP / (TP + FN).

        Recall measures how many actual vulnerabilities were detected.
        High recall = few missed vulnerabilities.

        Args:
            confusion: Confusion matrix

        Returns:
            Recall score (0.0 to 1.0)
        """
        denominator = confusion.true_positives + confusion.false_negatives
        if denominator == 0:
            return 0.0
        return confusion.true_positives / denominator

    def _calculate_f1(self, precision: float, recall: float) -> float:
        """
        Calculate F1 Score = 2 * (Precision * Recall) / (Precision + Recall).

        F1 is the harmonic mean of precision and recall.
        It provides a balanced measure of detection performance.

        Args:
            precision: Precision score
            recall: Recall score

        Returns:
            F1 score (0.0 to 1.0)
        """
        denominator = precision + recall
        if denominator == 0:
            return 0.0
        return 2 * (precision * recall) / denominator

    def _calculate_specificity(self, confusion: ConfusionMatrix) -> float:
        """
        Calculate Specificity (TNR) = TN / (TN + FP).

        Specificity measures how well secure code is correctly identified.
        High specificity = few false positives.

        Args:
            confusion: Confusion matrix

        Returns:
            Specificity score (0.0 to 1.0)
        """
        denominator = confusion.true_negatives + confusion.false_positives
        if denominator == 0:
            return 0.0
        return confusion.true_negatives / denominator

    def _calculate_accuracy(self, confusion: ConfusionMatrix) -> float:
        """
        Calculate Accuracy = (TP + TN) / Total.

        Accuracy measures overall correctness.
        Note: Can be misleading with imbalanced datasets.

        Args:
            confusion: Confusion matrix

        Returns:
            Accuracy score (0.0 to 1.0)
        """
        if confusion.total == 0:
            return 0.0
        return (confusion.true_positives + confusion.true_negatives) / confusion.total

    def _calculate_fpr(self, confusion: ConfusionMatrix) -> float:
        """
        Calculate False Positive Rate = FP / (FP + TN).

        FPR measures the rate of false alarms.
        Lower is better.

        Args:
            confusion: Confusion matrix

        Returns:
            False positive rate (0.0 to 1.0)
        """
        denominator = confusion.false_positives + confusion.true_negatives
        if denominator == 0:
            return 0.0
        return confusion.false_positives / denominator

    def _calculate_fnr(self, confusion: ConfusionMatrix) -> float:
        """
        Calculate False Negative Rate = FN / (FN + TP).

        FNR measures the rate of missed vulnerabilities.
        Lower is better.

        Args:
            confusion: Confusion matrix

        Returns:
            False negative rate (0.0 to 1.0)
        """
        denominator = confusion.false_negatives + confusion.true_positives
        if denominator == 0:
            return 0.0
        return confusion.false_negatives / denominator

    def get_weak_categories(
        self,
        category_metrics: list[CategoryMetrics],
        threshold: float = 0.6
    ) -> list[str]:
        """
        Identify weak categories based on F1 score threshold.

        Args:
            category_metrics: Per-category metrics
            threshold: F1 threshold below which a category is considered weak

        Returns:
            List of category names with F1 < threshold
        """
        weak = []
        for cat_metric in category_metrics:
            if cat_metric.metrics.f1_score < threshold:
                weak.append(cat_metric.category)
        return weak

    def get_strong_categories(
        self,
        category_metrics: list[CategoryMetrics],
        threshold: float = 0.6
    ) -> list[str]:
        """
        Identify strong categories based on F1 score threshold.

        Args:
            category_metrics: Per-category metrics
            threshold: F1 threshold at or above which a category is considered strong

        Returns:
            List of category names with F1 >= threshold
        """
        strong = []
        for cat_metric in category_metrics:
            if cat_metric.metrics.f1_score >= threshold:
                strong.append(cat_metric.category)
        return strong

    def compare_metrics(
        self,
        metrics1: EvaluationMetrics,
        metrics2: EvaluationMetrics
    ) -> dict[str, float]:
        """
        Compare two sets of metrics to detect performance changes.

        Args:
            metrics1: Earlier metrics
            metrics2: Later metrics

        Returns:
            Dictionary of metric changes (delta values)
        """
        return {
            "f1_change": metrics2.f1_score - metrics1.f1_score,
            "precision_change": metrics2.precision - metrics1.precision,
            "recall_change": metrics2.recall - metrics1.recall,
            "accuracy_change": metrics2.accuracy - metrics1.accuracy,
            "fpr_change": metrics2.false_positive_rate - metrics1.false_positive_rate,
            "fnr_change": metrics2.false_negative_rate - metrics1.false_negative_rate
        }

    def is_performance_stable(
        self,
        metrics1: EvaluationMetrics,
        metrics2: EvaluationMetrics,
        threshold: float = 0.05
    ) -> bool:
        """
        Determine if performance is stable between two evaluations.

        Args:
            metrics1: Earlier metrics
            metrics2: Later metrics
            threshold: Maximum F1 change to be considered stable

        Returns:
            True if F1 change is below threshold, False otherwise
        """
        f1_change = abs(metrics2.f1_score - metrics1.f1_score)
        return f1_change < threshold

    def analyze_confidence_distribution(
        self,
        results: list[TestResult]
    ) -> dict[str, Any]:
        """
        Analyze the distribution of confidence scores.

        Args:
            results: List of test results

        Returns:
            Dictionary with confidence analysis
        """
        if not results:
            return {}

        confidences = [r.confidence for r in results]

        # Split by correctness
        correct_confidences = [
            r.confidence for r in results
            if r.outcome in (DetectionOutcome.TRUE_POSITIVE, DetectionOutcome.TRUE_NEGATIVE)
        ]
        incorrect_confidences = [
            r.confidence for r in results
            if r.outcome in (DetectionOutcome.FALSE_POSITIVE, DetectionOutcome.FALSE_NEGATIVE)
        ]

        def stats(values):
            if not values:
                return {"mean": 0.0, "min": 0.0, "max": 0.0}
            return {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }

        return {
            "overall": stats(confidences),
            "correct_predictions": stats(correct_confidences),
            "incorrect_predictions": stats(incorrect_confidences),
            "total_results": len(results),
            "correct_count": len(correct_confidences),
            "incorrect_count": len(incorrect_confidences)
        }

    def generate_summary_report(
        self,
        overall_metrics: EvaluationMetrics,
        category_metrics: list[CategoryMetrics]
    ) -> dict[str, Any]:
        """
        Generate a comprehensive summary report.

        Args:
            overall_metrics: Overall evaluation metrics
            category_metrics: Per-category metrics

        Returns:
            Dictionary with complete summary
        """
        weak_categories = self.get_weak_categories(category_metrics)
        strong_categories = self.get_strong_categories(category_metrics)

        # Category performance ranking
        category_ranking = sorted(
            category_metrics,
            key=lambda x: x.metrics.f1_score,
            reverse=True
        )

        return {
            "overall_performance": {
                "f1_score": overall_metrics.f1_score,
                "precision": overall_metrics.precision,
                "recall": overall_metrics.recall,
                "accuracy": overall_metrics.accuracy,
                "specificity": overall_metrics.specificity
            },
            "confusion_matrix": {
                "true_positives": overall_metrics.confusion_matrix.true_positives,
                "true_negatives": overall_metrics.confusion_matrix.true_negatives,
                "false_positives": overall_metrics.confusion_matrix.false_positives,
                "false_negatives": overall_metrics.confusion_matrix.false_negatives
            },
            "error_rates": {
                "false_positive_rate": overall_metrics.false_positive_rate,
                "false_negative_rate": overall_metrics.false_negative_rate
            },
            "category_analysis": {
                "total_categories": len(category_metrics),
                "weak_categories": weak_categories,
                "strong_categories": strong_categories,
                "best_category": category_ranking[0].category if category_ranking else None,
                "worst_category": category_ranking[-1].category if category_ranking else None
            },
            "category_scores": {
                cm.category: cm.metrics.f1_score
                for cm in category_metrics
            },
            "total_samples": overall_metrics.total_samples
        }
