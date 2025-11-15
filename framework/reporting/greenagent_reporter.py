"""
Green Agent Reporter.

Generates reports for        report.append(f"# Green Agent Effectiveness Report\n\n")
        report.append(f"**Evaluation ID:** `{dual_result.evaluation_id}`\n")
        report.append(f"**Purple Agent Tested:** {dual_result.purple_agent_name}\n")
        report.append(f"**Scenario:** {dual_result.scenario}\n")
        report.append(f"**Date:** {dual_result.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Duration:** {dual_result.total_time_seconds:.1f} seconds\n\n")
        
        report.append("---\n\n")
        
        # Executive Summary
        report.append("## 📊 Executive Summary\n\n")
        report.append(f"**Evaluation Score:** {metrics.competition_score:.1f}/100 ({metrics.grade})\n\n") effectiveness metrics.
Focuses on attack effectiveness and security evaluation performance.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from framework.models import GreenAgentMetrics, DualEvaluationResult


class GreenAgentReporter:
    """
    Generates Green Agent effectiveness reports.
    
    Produces reports focused on:
    - Attack effectiveness (TP/FP/FN/TN)
    - Security evaluation metrics
    - Scanner performance analysis
    - Per-category breakdowns
    
    Audience: Red team, Security researchers, Evaluators
    """

    def __init__(self):
        """Initialize Green Agent reporter."""
        pass

    def generate_markdown_report(
        self,
        dual_result: DualEvaluationResult,
        include_categories: bool = True
    ) -> str:
        """
        Generate markdown format report for Green Agent metrics.

        Args:
            dual_result: Dual evaluation result
            include_categories: Whether to include per-category breakdowns

        Returns:
            Markdown formatted report
        """
        metrics = dual_result.green_agent_metrics
        
        report = []
        report.append("# Green Agent Effectiveness Report\n\n")
        report.append(f"**Evaluation ID:** `{dual_result.evaluation_id}`\n")
        report.append(f"**Purple Agent Tested:** {dual_result.purple_agent_name}\n")
        report.append(f"**Scenario:** {dual_result.scenario}\n")
        report.append(f"**Date:** {dual_result.end_time.strftime('%Y-%m-%d %H:%M:%S') if dual_result.end_time else 'In Progress'}\n")
        report.append(f"**Duration:** {dual_result.total_time_seconds:.1f} seconds\n\n")
        
        report.append("---\n\n")
        
        # Executive Summary
        report.append("## 📊 Executive Summary\n\n")
        report.append(f"**Evaluation Score:** {metrics.competition_score:.1f}/100 ({metrics.grade})\n\n")
        report.append(self._get_performance_status(metrics))
        report.append("\n\n---\n\n")
        
        # Classification Results
        report.append("## 🎯 Classification Results\n\n")
        report.append("### Confusion Matrix\n\n")
        report.append("|  | **Predicted Malicious** | **Predicted Benign** |\n")
        report.append("|---|---------------------|------------------|\n")
        report.append(f"| **Actually Malicious** | {metrics.true_positives} (TP) | {metrics.false_negatives} (FN) |\n")
        report.append(f"| **Actually Benign** | {metrics.false_positives} (FP) | {metrics.true_negatives} (TN) |\n\n")
        
        # Performance Metrics
        report.append("### Performance Metrics\n\n")
        report.append("| Metric | Score | Interpretation |\n")
        report.append("|--------|-------|----------------|\n")
        report.append(f"| **F1 Score** | {metrics.f1_score:.3f} | Overall detection effectiveness |\n")
        report.append(f"| **Precision** | {metrics.precision:.3f} | {metrics.precision*100:.1f}% of flagged items were actual vulnerabilities |\n")
        report.append(f"| **Recall** | {metrics.recall:.3f} | {metrics.recall*100:.1f}% of all vulnerabilities were discovered |\n")
        report.append(f"| **Accuracy** | {metrics.accuracy:.3f} | {metrics.accuracy*100:.1f}% correct classifications |\n")
        report.append(f"| **Specificity** | {metrics.specificity:.3f} | {metrics.specificity*100:.1f}% of benign inputs correctly passed |\n\n")
        
        # Error Analysis
        report.append("### Error Analysis\n\n")
        report.append(f"- **False Positive Rate:** {metrics.false_positive_rate*100:.1f}% (lower is better)\n")
        report.append(f"- **False Negative Rate:** {metrics.false_negative_rate*100:.1f}% (lower is better)\n\n")
        
        # Strengths and Weaknesses
        report.append(self._generate_strengths_weaknesses(metrics))
        report.append("\n---\n\n")
        
        # Resource Usage
        report.append("## 💰 Resource Usage\n\n")
        report.append(f"- **Total Tests:** {metrics.total_tests}\n")
        report.append(f"- **Total Cost:** ${metrics.total_cost_usd:.2f}\n")
        report.append(f"- **Cost per Test:** ${metrics.total_cost_usd/max(1, metrics.total_tests):.4f}\n")
        report.append(f"- **Average Latency:** {metrics.total_latency_ms/max(1, metrics.total_tests):.1f}ms per test\n\n")
        
        # Per-category breakdown
        if include_categories and metrics.per_category:
            report.append("---\n\n")
            report.append("## 📂 Per-Category Performance\n\n")
            report.append("| Category | F1 Score | Precision | Recall | Tests | Grade |\n")
            report.append("|----------|----------|-----------|--------|-------|-------|\n")
            
            for category, cat_metrics in sorted(metrics.per_category.items()):
                report.append(
                    f"| {category} | {cat_metrics.f1_score:.3f} | "
                    f"{cat_metrics.precision:.3f} | {cat_metrics.recall:.3f} | "
                    f"{cat_metrics.total_tests} | {cat_metrics.grade} |\n"
                )
            report.append("\n")
        
        report.append("---\n\n")
        report.append(f"*Report generated by Green Agent Effectiveness Reporter on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        return "".join(report)

    def _get_performance_status(self, metrics: GreenAgentMetrics) -> str:
        """Generate performance status message."""
        if metrics.f1_score >= 0.9:
            return "✅ **Status:** EXCELLENT - Top-tier scanner performance"
        elif metrics.f1_score >= 0.8:
            return "✅ **Status:** GOOD - Strong detection capabilities"
        elif metrics.f1_score >= 0.7:
            return "⚠️ **Status:** MODERATE - Acceptable but room for improvement"
        elif metrics.f1_score >= 0.6:
            return "⚠️ **Status:** FAIR - Needs improvement"
        else:
            return "❌ **Status:** POOR - Significant improvements needed"

    def _generate_strengths_weaknesses(self, metrics: GreenAgentMetrics) -> str:
        """Generate strengths and weaknesses analysis."""
        report = []
        report.append("### Strengths & Weaknesses\n\n")
        
        # Strengths
        report.append("**Strengths:**\n\n")
        if metrics.precision >= 0.9:
            report.append("- ✅ Excellent precision - very few false alarms\n")
        if metrics.recall >= 0.9:
            report.append("- ✅ Excellent recall - catches most vulnerabilities\n")
        if metrics.specificity >= 0.9:
            report.append("- ✅ Excellent specificity - doesn't break benign functionality\n")
        if metrics.false_positive_rate < 0.1:
            report.append("- ✅ Low false positive rate - high usability\n")
        if not any([metrics.precision >= 0.9, metrics.recall >= 0.9, 
                   metrics.specificity >= 0.9, metrics.false_positive_rate < 0.1]):
            report.append("- ⚠️ No outstanding strengths identified\n")
        
        report.append("\n**Weaknesses:**\n\n")
        if metrics.recall < 0.7:
            report.append(f"- ❌ Low recall ({metrics.recall:.1%}) - missing {metrics.false_negatives} vulnerabilities\n")
        if metrics.precision < 0.7:
            report.append(f"- ❌ Low precision ({metrics.precision:.1%}) - {metrics.false_positives} false alarms\n")
        if metrics.false_negative_rate > 0.2:
            report.append(f"- ❌ High false negative rate ({metrics.false_negative_rate:.1%}) - many evasions\n")
        if metrics.false_positive_rate > 0.2:
            report.append(f"- ❌ High false positive rate ({metrics.false_positive_rate:.1%}) - low usability\n")
        if not any([metrics.recall < 0.7, metrics.precision < 0.7,
                   metrics.false_negative_rate > 0.2, metrics.false_positive_rate > 0.2]):
            report.append("- ✅ No major weaknesses identified\n")
        
        return "".join(report)

    def generate_json_report(self, dual_result: DualEvaluationResult) -> Dict[str, Any]:
        """
        Generate JSON format report for Green Agent metrics.

        Args:
            dual_result: Dual evaluation result

        Returns:
            Dictionary suitable for JSON serialization
        """
        metrics = dual_result.green_agent_metrics
        
        return {
            "report_type": "green_agent_effectiveness",
            "evaluation_id": dual_result.evaluation_id,
            "purple_agent": dual_result.purple_agent_name,
            "scenario": dual_result.scenario,
            "timestamp": dual_result.end_time.isoformat() if dual_result.end_time else None,
            "duration_seconds": dual_result.total_time_seconds,
            
            "competition_metrics": {
                "score": metrics.competition_score,
                "grade": metrics.grade,
                "f1_score": metrics.f1_score
            },
            
            "classification": {
                "confusion_matrix": {
                    "true_positives": metrics.true_positives,
                    "true_negatives": metrics.true_negatives,
                    "false_positives": metrics.false_positives,
                    "false_negatives": metrics.false_negatives
                },
                "performance": {
                    "precision": metrics.precision,
                    "recall": metrics.recall,
                    "f1_score": metrics.f1_score,
                    "accuracy": metrics.accuracy,
                    "specificity": metrics.specificity
                },
                "error_rates": {
                    "false_positive_rate": metrics.false_positive_rate,
                    "false_negative_rate": metrics.false_negative_rate
                }
            },
            
            "resources": {
                "total_tests": metrics.total_tests,
                "total_cost_usd": metrics.total_cost_usd,
                "cost_per_test": metrics.total_cost_usd / max(1, metrics.total_tests),
                "total_latency_ms": metrics.total_latency_ms,
                "avg_latency_ms": metrics.total_latency_ms / max(1, metrics.total_tests)
            },
            
            "per_category": {
                category: {
                    "f1_score": cat_metrics.f1_score,
                    "precision": cat_metrics.precision,
                    "recall": cat_metrics.recall,
                    "grade": cat_metrics.grade,
                    "total_tests": cat_metrics.total_tests
                }
                for category, cat_metrics in metrics.per_category.items()
            } if metrics.per_category else {}
        }

    def generate_competition_summary(self, dual_result: DualEvaluationResult) -> str:
        """
        Generate brief competition summary for leaderboards.

        Args:
            dual_result: Dual evaluation result

        Returns:
            Brief summary string
        """
        metrics = dual_result.green_agent_metrics
        
        return (
            f"Score: {metrics.competition_score:.1f}/100 ({metrics.grade}) | "
            f"F1: {metrics.f1_score:.3f} | "
            f"Precision: {metrics.precision:.3f} | "
            f"Recall: {metrics.recall:.3f} | "
            f"Vulnerabilities Found: {metrics.true_positives} | "
            f"Tests: {metrics.total_tests}"
        )
