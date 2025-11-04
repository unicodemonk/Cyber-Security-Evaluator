"""
Tests for Baseline SQL Detector (Purple Agent).
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from purple_agents.baseline.sql_detector import BaselineSQLDetector


class TestBaselineSQLDetector:
    """Test suite for BaselineSQLDetector."""

    @pytest.fixture
    def detector(self):
        """Fixture providing BaselineSQLDetector instance."""
        return BaselineSQLDetector()

    def test_detect_python_f_string_vulnerable(self, detector):
        """Test detection of f-string SQL injection."""
        code = '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id={user_id}"
    cursor.execute(query)
    return cursor.fetchone()
'''
        result = detector.analyze("test_1", code, "python")

        assert result.is_vulnerable == True
        assert result.confidence > 0.5
        assert result.severity in ["critical", "high"]

        print(f"\n✓ Detected f-string vulnerability:")
        print(f"  - Vulnerable: {result.is_vulnerable}")
        print(f"  - Confidence: {result.confidence:.2f}")
        print(f"  - Severity: {result.severity}")

    def test_detect_python_concatenation_vulnerable(self, detector):
        """Test detection of string concatenation SQL injection."""
        code = '''
def search_products(keyword):
    sql = "SELECT * FROM products WHERE name LIKE '%" + keyword + "%'"
    return db.execute(sql).fetchall()
'''
        result = detector.analyze("test_2", code, "python")

        assert result.is_vulnerable == True
        assert result.confidence > 0.5
        assert len(result.detected_patterns) > 0

        print(f"\n✓ Detected concatenation vulnerability:")
        print(f"  - Patterns: {len(result.detected_patterns)}")
        print(f"  - Explanation: {result.explanation}")

    def test_detect_python_format_vulnerable(self, detector):
        """Test detection of % formatting SQL injection."""
        code = '''
username = request.POST['username']
password = request.POST['password']
query = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (username, password)
cursor.execute(query)
'''
        result = detector.analyze("test_3", code, "python")

        assert result.is_vulnerable == True
        assert result.severity == "critical"

        print(f"\n✓ Detected % formatting vulnerability")

    def test_detect_python_parameterized_secure(self, detector):
        """Test detection of secure parameterized query."""
        code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id=?"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()
'''
        result = detector.analyze("test_4", code, "python")

        assert result.is_vulnerable == False
        # Either detects parameterized pattern or finds no vulnerabilities
        assert "parameterized" in result.explanation.lower() or "no obvious" in result.explanation.lower()

        print(f"\n✓ Correctly identified secure code:")
        print(f"  - Vulnerable: {result.is_vulnerable}")
        print(f"  - Explanation: {result.explanation}")

    def test_detect_python_orm_secure(self, detector):
        """Test detection of secure ORM usage."""
        code = '''
def filter_products(category):
    products = Product.objects.filter(category=category)
    return products
'''
        result = detector.analyze("test_5", code, "python")

        assert result.is_vulnerable == False

        print(f"\n✓ Correctly identified ORM secure code")

    def test_detect_javascript_template_literal_vulnerable(self, detector):
        """Test detection of JavaScript template literal SQL injection."""
        code = '''
function getUser(userId) {
    const query = `SELECT * FROM users WHERE id=${userId}`;
    return db.query(query);
}
'''
        result = detector.analyze("test_6", code, "javascript")

        assert result.is_vulnerable == True
        assert result.confidence > 0.5

        print(f"\n✓ Detected JavaScript template literal vulnerability")

    def test_detect_multiple_vulnerabilities(self, detector):
        """Test detection of code with multiple vulnerabilities."""
        code = '''
def get_data(user_id, table):
    query1 = f"SELECT * FROM {table} WHERE id={user_id}"
    query2 = "DELETE FROM logs WHERE user=" + str(user_id)
    cursor.execute(query1)
    cursor.execute(query2)
'''
        result = detector.analyze("test_7", code, "python")

        assert result.is_vulnerable == True
        assert len(result.detected_patterns) >= 2  # Multiple patterns detected

        print(f"\n✓ Detected multiple vulnerabilities:")
        print(f"  - Patterns detected: {len(result.detected_patterns)}")
        print(f"  - Confidence: {result.confidence:.2f}")

    def test_line_number_detection(self, detector):
        """Test that line numbers are correctly identified."""
        code = '''def safe_query():
    query = "SELECT * FROM users WHERE id=?"
    cursor.execute(query, (1,))

def vulnerable_query(uid):
    query = f"SELECT * FROM users WHERE id={uid}"
    cursor.execute(query)
'''
        result = detector.analyze("test_8", code, "python")

        assert result.is_vulnerable == True
        assert len(result.line_numbers) > 0
        # The vulnerable line should be around line 6
        assert any(5 <= ln <= 7 for ln in result.line_numbers)

        print(f"\n✓ Line numbers detected: {result.line_numbers}")

    def test_confidence_levels(self, detector):
        """Test that confidence varies appropriately."""
        # Clear vulnerability
        vuln_code = 'query = f"SELECT * FROM users WHERE id={user_id}"'
        vuln_result = detector.analyze("test_9", vuln_code, "python")

        # Clear secure code
        secure_code = 'cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))'
        secure_result = detector.analyze("test_10", secure_code, "python")

        # Vulnerable should have high confidence
        assert vuln_result.is_vulnerable == True
        assert vuln_result.confidence > 0.7

        # Secure should have moderate confidence (can't be 100% sure without deeper analysis)
        assert secure_result.is_vulnerable == False
        assert secure_result.confidence > 0.5

        print(f"\n✓ Confidence levels:")
        print(f"  - Vulnerable: {vuln_result.confidence:.2f}")
        print(f"  - Secure: {secure_result.confidence:.2f}")

    def test_nosql_injection_detection(self, detector):
        """Test NoSQL injection detection."""
        code = '''
def find_user(username, password):
    query = {"$where": f"this.username == '{username}' && this.password == '{password}'"}
    user = db.users.find_one(query)
    return user
'''
        result = detector.analyze("test_11", code, "python")

        assert result.is_vulnerable == True
        assert result.confidence > 0.5

        print(f"\n✓ Detected NoSQL injection vulnerability")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
