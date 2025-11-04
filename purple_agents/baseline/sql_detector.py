"""
Baseline SQL Injection Detector - Purple Agent Implementation.

This is a reference implementation of a Purple Agent that detects SQL injection
vulnerabilities using pattern matching. Serves as a baseline for comparison
and testing the Green Agent evaluation framework.
"""

import re
import argparse
import logging
from typing import Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class DetectionRequest(BaseModel):
    """Request model for SQL injection detection."""
    test_case_id: str
    code: str
    language: str
    category: str | None = None


class DetectionResponse(BaseModel):
    """Response model for SQL injection detection."""
    test_case_id: str
    is_vulnerable: bool
    confidence: float = 0.5
    vulnerability_type: str | None = None
    explanation: str | None = None
    detected_patterns: list[str] = []
    line_numbers: list[int] = []
    severity: str | None = None


# ============================================================================
# Baseline SQL Injection Detector
# ============================================================================

class BaselineSQLDetector:
    """
    Baseline SQL injection detector using pattern matching.

    This detector uses regex patterns to identify common SQL injection
    vulnerabilities. It's not perfect but provides a reasonable baseline
    for evaluating the Green Agent's evaluation capabilities.
    """

    # Vulnerable patterns for different languages
    PYTHON_VULNERABLE_PATTERNS = [
        # F-string interpolation
        (r'f["\'].*SELECT.*\{.*\}', "f-string SQL interpolation", "critical"),
        (r'f["\'].*INSERT.*\{.*\}', "f-string SQL interpolation", "critical"),
        (r'f["\'].*UPDATE.*\{.*\}', "f-string SQL interpolation", "critical"),
        (r'f["\'].*DELETE.*\{.*\}', "f-string SQL interpolation", "critical"),

        # String concatenation with +
        (r'["\'].*SELECT.*["\']\s*\+\s*\w+', "String concatenation in SQL", "critical"),
        (r'["\'].*INSERT.*["\']\s*\+\s*\w+', "String concatenation in SQL", "critical"),
        (r'["\'].*UPDATE.*["\']\s*\+\s*\w+', "String concatenation in SQL", "critical"),
        (r'["\'].*DELETE.*["\']\s*\+\s*\w+', "String concatenation in SQL", "critical"),

        # % formatting
        (r'["\'].*SELECT.*["\'].*%\s*\(', "% formatting in SQL", "critical"),
        (r'["\'].*SELECT.*["\'].*%\s*\w+', "% formatting in SQL", "critical"),

        # .format() usage
        (r'["\'].*SELECT.*["\']\s*\.format\(', ".format() in SQL", "critical"),

        # execute with f-string or concatenation
        (r'\.execute\s*\(\s*f["\']', "execute() with f-string", "critical"),
        (r'\.execute\s*\(\s*["\'].*["\']\s*\+', "execute() with concatenation", "critical"),

        # Django/ORM unsafe patterns
        (r'\.extra\s*\(.*where\s*=\s*\[.*f["\']', "Django .extra() with f-string", "high"),
        (r'\.raw\s*\(.*f["\']', "Django .raw() with f-string", "high"),

        # MongoDB $where with string interpolation
        (r'\$where.*f["\']', "MongoDB $where with f-string", "critical"),
    ]

    JAVASCRIPT_VULNERABLE_PATTERNS = [
        # Template literals
        (r'`.*SELECT.*\$\{.*\}`', "Template literal SQL interpolation", "critical"),
        (r'`.*INSERT.*\$\{.*\}`', "Template literal SQL interpolation", "critical"),

        # String concatenation
        (r'["\'].*SELECT.*["\']\s*\+\s*\w+', "String concatenation in SQL", "critical"),
        (r'["\'].*INSERT.*["\']\s*\+\s*\w+', "String concatenation in SQL", "critical"),

        # Query execution with concatenation
        (r'\.query\s*\(\s*["\'].*["\']\s*\+', "query() with concatenation", "critical"),
        (r'\.execute\s*\(\s*`', "execute() with template literal", "critical"),
    ]

    JAVA_VULNERABLE_PATTERNS = [
        # String concatenation
        (r'["\'].*SELECT.*["\']\s*\+\s*\w+', "String concatenation in SQL", "critical"),
        (r'Statement.*executeQuery\s*\(.*\+', "executeQuery with concatenation", "critical"),
        (r'createQuery\s*\(.*\+', "createQuery with concatenation", "high"),

        # String.format usage
        (r'String\.format\s*\(["\'].*SELECT', "String.format in SQL", "critical"),
    ]

    PHP_VULNERABLE_PATTERNS = [
        # Variable interpolation in double quotes
        (r'".*SELECT.*\$\w+"', "Variable interpolation in SQL", "critical"),
        (r'".*INSERT.*\$\w+"', "Variable interpolation in SQL", "critical"),

        # Concatenation
        (r'["\'].*SELECT.*["\']\s*\.\s*\$', "String concatenation in SQL", "critical"),

        # mysql_query with variables
        (r'mysql_query\s*\(.*\$\w+', "mysql_query with variable", "critical"),
    ]

    # Safe patterns that indicate proper parameterization
    PYTHON_SAFE_PATTERNS = [
        r'\.execute\s*\(["\'].*\?.*["\'],\s*\(',  # Parameterized with ?
        r'\.execute\s*\(["\'].*%s.*["\'],\s*\(',  # Parameterized with %s
        r'\.execute\s*\(["\'].*:[\w]+.*["\']',    # Named parameters
        r'\.filter\s*\(',                          # ORM filter()
        r'\.objects\.filter',                      # Django ORM
        r'\.find_one\s*\(\s*\{["\']',             # MongoDB safe query
    ]

    def __init__(self):
        """Initialize the baseline detector."""
        self.patterns_by_language = {
            "python": self.PYTHON_VULNERABLE_PATTERNS,
            "javascript": self.JAVASCRIPT_VULNERABLE_PATTERNS,
            "java": self.JAVA_VULNERABLE_PATTERNS,
            "php": self.PHP_VULNERABLE_PATTERNS,
        }

    def analyze(self, test_case_id: str, code: str, language: str, category: str | None = None) -> DetectionResponse:
        """
        Analyze code for SQL injection vulnerabilities.

        Args:
            test_case_id: Test case identifier
            code: Code to analyze
            language: Programming language
            category: SQL injection category hint

        Returns:
            DetectionResponse with detection results
        """
        language = language.lower()

        # First check for safe patterns (high confidence it's secure)
        if language == "python":
            for safe_pattern in self.PYTHON_SAFE_PATTERNS:
                if re.search(safe_pattern, code, re.IGNORECASE | re.MULTILINE):
                    return DetectionResponse(
                        test_case_id=test_case_id,
                        is_vulnerable=False,
                        confidence=0.8,
                        explanation="Code uses parameterized queries or ORM safe methods",
                        detected_patterns=["parameterized_query"]
                    )

        # Check for vulnerable patterns
        patterns = self.patterns_by_language.get(language, [])
        detected_vulnerabilities = []
        detected_patterns = []
        line_numbers = []
        max_severity = "low"

        for pattern, description, severity in patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                detected_vulnerabilities.append(description)
                detected_patterns.append(pattern)

                # Find line number
                line_num = code[:match.start()].count('\n') + 1
                line_numbers.append(line_num)

                # Track highest severity
                if severity == "critical":
                    max_severity = "critical"
                elif severity == "high" and max_severity != "critical":
                    max_severity = "high"

        # Determine result
        if detected_vulnerabilities:
            # Vulnerable
            confidence = min(0.95, 0.7 + (len(detected_vulnerabilities) * 0.05))
            explanation = f"Detected {len(detected_vulnerabilities)} potential SQL injection(s): {', '.join(set(detected_vulnerabilities))}"

            return DetectionResponse(
                test_case_id=test_case_id,
                is_vulnerable=True,
                confidence=confidence,
                vulnerability_type="SQL Injection",
                explanation=explanation,
                detected_patterns=list(set(detected_patterns)),
                line_numbers=sorted(set(line_numbers)),
                severity=max_severity
            )
        else:
            # No vulnerabilities detected
            # Lower confidence because absence of evidence isn't evidence of absence
            return DetectionResponse(
                test_case_id=test_case_id,
                is_vulnerable=False,
                confidence=0.6,
                explanation="No obvious SQL injection patterns detected",
                detected_patterns=[]
            )


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Baseline SQL Injection Detector",
    description="Purple Agent for detecting SQL injection vulnerabilities",
    version="1.0.0"
)

detector = BaselineSQLDetector()


@app.post("/detect", response_model=DetectionResponse)
async def detect_sql_injection(request: DetectionRequest) -> DetectionResponse:
    """
    Analyze code for SQL injection vulnerabilities.

    Args:
        request: Detection request with code sample

    Returns:
        Detection response with results
    """
    try:
        logger.info(f"Analyzing test case: {request.test_case_id} ({request.language})")

        result = detector.analyze(
            test_case_id=request.test_case_id,
            code=request.code,
            language=request.language,
            category=request.category
        )

        logger.info(f"Result: {request.test_case_id} -> vulnerable={result.is_vulnerable}, "
                   f"confidence={result.confidence:.2f}")

        return result

    except Exception as e:
        logger.error(f"Detection failed for {request.test_case_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "detector": "baseline_sql_injection"}


@app.get("/")
async def root():
    """Root endpoint with agent information."""
    return {
        "name": "Baseline SQL Injection Detector",
        "version": "1.0.0",
        "type": "purple_agent",
        "description": "Pattern-based SQL injection vulnerability detector",
        "endpoints": {
            "detect": "/detect",
            "health": "/health"
        }
    }


def main():
    """Main entry point for running the Purple Agent."""
    parser = argparse.ArgumentParser(description="Baseline SQL Injection Detector - Purple Agent")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting Baseline SQL Detector on {args.host}:{args.port}")

    uvicorn.run(
        "sql_detector:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
