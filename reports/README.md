# Test Reports

**Test Date:** November 14, 2025, 17:12:51  
**Target:** Home Automation Agent  
**Framework:** SecurityEvaluator with Dual Evaluation

---

## 📁 Available Reports

### 1. FINAL_EVALUATION_REPORT_20251114_171251.md
**Complete Test Results** - 18 KB

Comprehensive report containing:
- ✅ Both MITRE Direct Attack (53 tests) and Multi-Agent Framework (129 tests) results
- ✅ Detailed attack enumeration with payloads and outcomes
- ✅ MITRE technique coverage and distribution
- ✅ Complete metrics for both perspectives

**Best for:** Technical teams who want full details

---

### 2. GREEN_AGENT_REPORT_20251114_171251.md
**Security Evaluator Perspective** - 1.6 KB

Focused on attack effectiveness:
- **Evaluation Score:** 63.2/100 (Grade: D)
- **F1 Score:** 0.632
- **Precision:** 92.3% (high accuracy)
- **Recall:** 48.0% (needs improvement)
- Confusion matrix and error analysis

**Best for:** Red teams, Security researchers, Evaluators

---

### 3. PURPLE_AGENT_REPORT_20251114_171251.md
**Security Posture Assessment** - 9.7 KB

Focused on system security:
- **Security Score:** 48.0/100
- **Risk Level:** 🔴 HIGH
- **Vulnerabilities:** 26 (all HIGH severity, CVSS 7.3)
- Detailed vulnerability descriptions
- Remediation roadmap with time estimates

**Best for:** Defenders, Security teams, Management, Compliance

---

## 📊 Quick Results Summary

| Perspective | Score | Status | Key Insight |
|------------|-------|--------|-------------|
| **Green Agent** | 63.2/100 (D) | Needs Improvement | High precision (92.3%) but low recall (48%) |
| **Purple Agent** | 48.0/100 | 🔴 HIGH RISK | 26 vulnerabilities, 52% attack success rate |

---

## 📚 Understanding the Reports

For a complete explanation of how the dual evaluation framework works and how to interpret these reports, see:

**→ `/docs/DUAL_EVALUATION_GUIDE.md`**

This guide explains:
- How test outcomes (TP/FP/TN/FN) map to scores
- Why there are two different scores (63.2 vs 48.0)
- How to use each report for your role
- Detailed examples and correlations
- FAQ and troubleshooting

---

## 📦 Data Exports (JSON)

The following JSON files contain raw data for programmatic access:

- `FINAL_EVALUATION_DATA_20251114_171251.json` (144 KB) - Complete test data
- `dual_evaluation_FINAL_TEST_20251114_171251_20251114_171251.json` (33 KB) - Dual evaluation data
- `green_agent_FINAL_TEST_20251114_171251_20251114_171251.json` (486 B) - Green metrics
- `purple_agent_FINAL_TEST_20251114_171251_20251114_171251.json` (31 KB) - Purple assessment

---

## 🎯 Quick Actions

**If you're a Red Team / Researcher:**
→ Read `GREEN_AGENT_REPORT_20251114_171251.md`  
→ Focus on improving recall (currently 48%)  
→ Add more attack variants to increase coverage

**If you're a Defender / Security Team:**
→ Read `PURPLE_AGENT_REPORT_20251114_171251.md`  
→ Fix the 26 HIGH severity vulnerabilities  
→ Follow the Phase 1 remediation roadmap (2-4 hours)

**If you want complete details:**
→ Read `FINAL_EVALUATION_REPORT_20251114_171251.md`  
→ Review all 53 attack payloads and outcomes  
→ Analyze MITRE technique distribution

**If you want to understand the framework:**
→ Read `/docs/DUAL_EVALUATION_GUIDE.md`  
→ Learn how TP/FP/TN/FN map to scores  
→ Understand why there are two perspectives

---

*For questions about the framework, see `/docs/DUAL_EVALUATION_GUIDE.md`*
