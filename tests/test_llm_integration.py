"""
Tests for LLM Integration System.

Run with: pytest tests/test_llm_integration.py -v
"""

import pytest
import json
from pathlib import Path

# Import LLM components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm import (
    PromptManager,
    PromptRenderer,
    extract_json,
    parse_json_response,
    parse_boolean_response,
    parse_confidence_score,
    extract_code_blocks,
    extract_list_items,
    extract_key_value_pairs,
)


# ============================================================================
# Prompt Renderer Tests
# ============================================================================

class TestPromptRenderer:
    """Test prompt rendering functionality."""

    def test_simple_placeholder(self):
        """Test simple placeholder replacement."""
        renderer = PromptRenderer()
        template = "Hello {{name}}! You are {{age}} years old."
        context = {"name": "Alice", "age": 25}

        result = renderer.render(template, context)
        assert result == "Hello Alice! You are 25 years old."

    def test_list_iteration(self):
        """Test list iteration."""
        renderer = PromptRenderer()
        template = "Items:\n{{#items}}- {{.}}\n{{/items}}"
        context = {"items": ["apple", "banana", "cherry"]}

        result = renderer.render(template, context)
        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result

    def test_list_with_dicts(self):
        """Test list iteration with dictionaries."""
        renderer = PromptRenderer()
        template = "{{#users}}User {{id}}: {{name}}\n{{/users}}"
        context = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        }

        result = renderer.render(template, context)
        assert "User 1: Alice" in result
        assert "User 2: Bob" in result

    def test_conditional_true(self):
        """Test conditional block when true."""
        renderer = PromptRenderer()
        template = "{{#show}}This should appear{{/show}}"
        context = {"show": True}

        result = renderer.render(template, context)
        assert "This should appear" in result

    def test_conditional_false(self):
        """Test conditional block when false."""
        renderer = PromptRenderer()
        template = "{{#show}}This should NOT appear{{/show}}"
        context = {"show": False}

        result = renderer.render(template, context)
        assert "This should NOT appear" not in result

    def test_empty_list(self):
        """Test empty list handling."""
        renderer = PromptRenderer()
        template = "{{#items}}Item: {{.}}{{/items}}"
        context = {"items": []}

        result = renderer.render(template, context)
        assert result == ""

    def test_nested_context(self):
        """Test nested data in context."""
        renderer = PromptRenderer()
        template = "{{#items}}{{name}}: {{value}}\n{{/items}}"
        context = {
            "items": [
                {"name": "x", "value": 10},
                {"name": "y", "value": 20},
            ]
        }

        result = renderer.render(template, context)
        assert "x: 10" in result
        assert "y: 20" in result

    def test_extract_placeholders(self):
        """Test placeholder extraction."""
        renderer = PromptRenderer()
        template = "Hello {{name}}, analyze {{code}} in {{language}}"

        placeholders = renderer.extract_placeholders(template)
        assert set(placeholders) == {"name", "code", "language"}

    def test_extract_block_placeholders(self):
        """Test extraction of block placeholders."""
        renderer = PromptRenderer()
        template = "{{#items}}{{name}}{{/items}}"

        placeholders = renderer.extract_placeholders(template)
        assert "items" in placeholders
        assert "name" in placeholders


# ============================================================================
# Prompt Manager Tests
# ============================================================================

class TestPromptManager:
    """Test prompt manager functionality."""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt manager with test prompts."""
        prompts_path = Path(__file__).parent.parent / "llm" / "prompts.yaml"
        return PromptManager(prompts_path)

    def test_load_prompts(self, prompt_manager):
        """Test loading prompts from YAML."""
        assert len(prompt_manager.templates) > 0
        assert "analyze_sql_injection" in prompt_manager.templates

    def test_list_prompts(self, prompt_manager):
        """Test listing available prompts."""
        prompts = prompt_manager.list_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) > 0

    def test_get_template(self, prompt_manager):
        """Test getting a template."""
        template = prompt_manager.get_template("analyze_sql_injection")
        assert template.key == "analyze_sql_injection"
        assert template.user is not None

    def test_get_invalid_template(self, prompt_manager):
        """Test getting non-existent template."""
        with pytest.raises(KeyError):
            prompt_manager.get_template("nonexistent_prompt")

    def test_validate_context(self, prompt_manager):
        """Test context validation."""
        template = prompt_manager.get_template("analyze_sql_injection")
        context = {
            "code": "SELECT * FROM users",
            "language": "sql",
            "category": "test",
        }

        missing = prompt_manager.validate_context(template, context)
        assert len(missing) == 0

    def test_validate_context_missing(self, prompt_manager):
        """Test context validation with missing fields."""
        template = prompt_manager.get_template("analyze_sql_injection")
        context = {"code": "SELECT * FROM users"}  # Missing language and category

        missing = prompt_manager.validate_context(template, context)
        assert len(missing) > 0
        assert "language" in missing
        assert "category" in missing

    def test_render_prompt(self, prompt_manager):
        """Test prompt rendering."""
        rendered = prompt_manager.render("analyze_sql_injection", {
            "code": "SELECT * FROM users WHERE id=1",
            "language": "python",
            "category": "classic_sqli",
        })

        assert rendered.user_prompt is not None
        assert "SELECT * FROM users WHERE id=1" in rendered.user_prompt
        assert "python" in rendered.user_prompt
        assert rendered.response_format == "json"

    def test_render_with_missing_required(self, prompt_manager):
        """Test rendering with missing required fields."""
        with pytest.raises(ValueError, match="Missing required placeholders"):
            prompt_manager.render("analyze_sql_injection", {
                "code": "SELECT * FROM users",
                # Missing language and category
            })

    def test_render_without_validation(self, prompt_manager):
        """Test rendering without validation."""
        rendered = prompt_manager.render(
            "analyze_sql_injection",
            {"code": "test"},  # Missing fields
            validate=False
        )
        assert rendered is not None


# ============================================================================
# Response Parser Tests
# ============================================================================

class TestResponseParser:
    """Test response parsing utilities."""

    def test_extract_json_plain(self):
        """Test extracting plain JSON."""
        text = '{"key": "value", "number": 42}'
        result = extract_json(text)
        assert result == {"key": "value", "number": 42}

    def test_extract_json_with_text(self):
        """Test extracting JSON from text with extra content."""
        text = 'Here is the result: {"key": "value"} and more text'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_code_block(self):
        """Test extracting JSON from code block."""
        text = '```json\n{"key": "value"}\n```'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_malformed(self):
        """Test handling malformed JSON."""
        text = "This is not JSON at all"
        result = extract_json(text)
        assert result is None

    def test_parse_boolean_yes(self):
        """Test parsing 'yes' as boolean."""
        assert parse_boolean_response("Yes") == True
        assert parse_boolean_response("yes, it is vulnerable") == True

    def test_parse_boolean_no(self):
        """Test parsing 'no' as boolean."""
        assert parse_boolean_response("No") == False
        assert parse_boolean_response("no, it's safe") == False

    def test_parse_boolean_json(self):
        """Test parsing boolean from JSON."""
        text = '{"is_vulnerable": true}'
        result = parse_boolean_response(text)
        assert result == True

    def test_parse_confidence_percentage(self):
        """Test parsing confidence from percentage."""
        assert parse_confidence_score("85%") == 0.85
        assert parse_confidence_score("confidence: 90%") == 0.90

    def test_parse_confidence_decimal(self):
        """Test parsing confidence from decimal."""
        assert parse_confidence_score("0.75") == 0.75
        assert parse_confidence_score("confidence: 0.88") == 0.88

    def test_parse_confidence_json(self):
        """Test parsing confidence from JSON."""
        text = '{"confidence": 0.95}'
        result = parse_confidence_score(text)
        assert result == 0.95

    def test_extract_code_blocks_python(self):
        """Test extracting Python code blocks."""
        text = """
        Here is some code:
        ```python
        def hello():
            print("world")
        ```
        """
        blocks = extract_code_blocks(text, language="python")
        assert len(blocks) == 1
        assert "def hello()" in blocks[0]

    def test_extract_code_blocks_any(self):
        """Test extracting any code blocks."""
        text = """
        ```python
        print("hello")
        ```
        ```javascript
        console.log("world")
        ```
        """
        blocks = extract_code_blocks(text)
        assert len(blocks) == 2

    def test_extract_list_items_numbered(self):
        """Test extracting numbered list items."""
        text = """
        1. First item
        2. Second item
        3. Third item
        """
        items = extract_list_items(text, numbered=True, bulleted=False)
        assert len(items) == 3
        assert "First item" in items

    def test_extract_list_items_bulleted(self):
        """Test extracting bulleted list items."""
        text = """
        - First item
        * Second item
        • Third item
        """
        items = extract_list_items(text, numbered=False, bulleted=True)
        assert len(items) == 3

    def test_extract_key_value_pairs(self):
        """Test extracting key-value pairs."""
        text = """
        Name: John Doe
        Age: 30
        City: New York
        """
        pairs = extract_key_value_pairs(text)
        assert pairs["Name"] == "John Doe"
        assert pairs["Age"] == "30"
        assert pairs["City"] == "New York"

    def test_extract_key_value_equals(self):
        """Test extracting key=value pairs."""
        text = """
        language = python
        version = 3.9
        """
        pairs = extract_key_value_pairs(text)
        assert pairs["language"] == "python"
        assert pairs["version"] == "3.9"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def prompt_manager(self):
        """Create prompt manager."""
        prompts_path = Path(__file__).parent.parent / "llm" / "prompts.yaml"
        return PromptManager(prompts_path)

    def test_full_prompt_workflow(self, prompt_manager):
        """Test complete prompt rendering workflow."""
        # Render prompt
        rendered = prompt_manager.render("analyze_sql_injection", {
            "code": "SELECT * FROM users WHERE id=" + "user_input",
            "language": "python",
            "category": "classic_sqli",
        })

        # Validate rendered prompt
        assert rendered.user_prompt is not None
        assert rendered.system_prompt is not None
        assert rendered.response_format == "json"
        assert rendered.temperature == 0.2

        # Simulate LLM response
        mock_response = {
            "is_vulnerable": True,
            "confidence": 0.95,
            "explanation": "String concatenation in SQL query",
        }

        # Parse response
        result = parse_json_response(json.dumps(mock_response))
        assert result["is_vulnerable"] == True
        assert result["confidence"] == 0.95

    def test_list_rendering_workflow(self, prompt_manager):
        """Test rendering with list data."""
        rendered = prompt_manager.render("evaluate_code_quality", {
            "code": "def test(): pass",
            "language": "python",
            "focus_areas": ["security", "performance", "readability"],
        })

        assert "security" in rendered.user_prompt
        assert "performance" in rendered.user_prompt
        assert "readability" in rendered.user_prompt


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
