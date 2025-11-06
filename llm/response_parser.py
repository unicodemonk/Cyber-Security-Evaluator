"""
Response Parser Utilities for LLM Responses.

Provides utilities for:
- Parsing JSON responses
- Extracting structured data
- Validating responses against schemas
- Handling malformed responses
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ValidationError


logger = logging.getLogger(__name__)


T = TypeVar('T', bound=BaseModel)


# ============================================================================
# JSON Parsing
# ============================================================================

def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text, handling common issues.

    Handles:
    - JSON wrapped in code blocks
    - Extra text before/after JSON
    - Malformed JSON

    Args:
        text: Text potentially containing JSON

    Returns:
        Parsed JSON dict or None if not found
    """
    # Try direct parsing first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract from code blocks
    code_block_pattern = r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    if matches:
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    # Try to find any JSON object or array
    json_pattern = r'(\{.*?\}|\[.*?\])'
    matches = re.findall(json_pattern, text, re.DOTALL)
    if matches:
        # Try each match, longest first (more likely to be complete)
        for match in sorted(matches, key=len, reverse=True):
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

    # Try to fix common issues
    fixed_text = fix_common_json_issues(text)
    try:
        return json.loads(fixed_text)
    except json.JSONDecodeError:
        pass

    logger.warning(f"Could not extract valid JSON from text: {text[:200]}...")
    return None


def fix_common_json_issues(text: str) -> str:
    """
    Fix common JSON formatting issues.

    Args:
        text: Potentially malformed JSON

    Returns:
        Fixed JSON string
    """
    # Remove trailing commas
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)

    # Fix single quotes (if no escaped quotes inside)
    if "'" in text and '"' not in text:
        text = text.replace("'", '"')

    # Remove comments (not valid JSON but sometimes LLMs add them)
    text = re.sub(r'//.*?\n', '\n', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    return text


def parse_json_response(
    text: str,
    model: Optional[Type[T]] = None,
    strict: bool = False,
) -> Union[Dict[str, Any], T]:
    """
    Parse JSON response from LLM and optionally validate with Pydantic model.

    Args:
        text: Response text
        model: Optional Pydantic model to validate against
        strict: If True, raise error if parsing fails; otherwise return empty dict/object

    Returns:
        Parsed JSON dict or Pydantic model instance

    Raises:
        ValueError: If strict=True and parsing fails
        ValidationError: If strict=True and validation fails
    """
    # Extract JSON
    data = extract_json(text)

    if data is None:
        if strict:
            raise ValueError(f"Could not extract valid JSON from response: {text[:200]}...")
        logger.warning("Failed to parse JSON, returning empty dict")
        return {} if model is None else model()

    # Validate with Pydantic model if provided
    if model:
        try:
            return model(**data)
        except ValidationError as e:
            if strict:
                raise
            logger.warning(f"JSON validation failed: {e}")
            return model()

    return data


# ============================================================================
# Structured Data Extraction
# ============================================================================

def extract_code_blocks(text: str, language: Optional[str] = None) -> List[str]:
    """
    Extract code blocks from markdown-formatted text.

    Args:
        text: Text containing code blocks
        language: Optional language filter (e.g., "python", "json")

    Returns:
        List of code block contents
    """
    if language:
        pattern = rf'```{language}\s*(.*?)```'
    else:
        pattern = r'```(?:\w+)?\s*(.*?)```'

    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]


def extract_list_items(text: str, numbered: bool = True, bulleted: bool = True) -> List[str]:
    """
    Extract list items from text.

    Args:
        text: Text containing lists
        numbered: Whether to extract numbered lists (1., 2., etc.)
        bulleted: Whether to extract bulleted lists (-, *, •, etc.)

    Returns:
        List of extracted items
    """
    items = []

    if numbered:
        # Match: 1. Item, 2. Item, etc.
        numbered_pattern = r'^\s*\d+\.\s+(.+)$'
        items.extend(re.findall(numbered_pattern, text, re.MULTILINE))

    if bulleted:
        # Match: - Item, * Item, • Item
        bullet_pattern = r'^\s*[-*•]\s+(.+)$'
        items.extend(re.findall(bullet_pattern, text, re.MULTILINE))

    return items


def extract_key_value_pairs(text: str) -> Dict[str, str]:
    """
    Extract key-value pairs from text.

    Handles formats like:
    - Key: Value
    - **Key**: Value
    - Key = Value

    Args:
        text: Text containing key-value pairs

    Returns:
        Dictionary of extracted pairs
    """
    pairs = {}

    # Pattern: Key: Value or **Key**: Value
    pattern1 = r'\*{0,2}([^:\n]+)\*{0,2}:\s*([^\n]+)'
    matches1 = re.findall(pattern1, text)
    for key, value in matches1:
        pairs[key.strip()] = value.strip()

    # Pattern: Key = Value
    pattern2 = r'([^=\n]+)\s*=\s*([^\n]+)'
    matches2 = re.findall(pattern2, text)
    for key, value in matches2:
        k = key.strip()
        if k not in pairs:  # Don't override existing
            pairs[k] = value.strip()

    return pairs


# ============================================================================
# Boolean/Classification Responses
# ============================================================================

def parse_boolean_response(text: str, default: Optional[bool] = None) -> Optional[bool]:
    """
    Parse boolean response from LLM.

    Recognizes: yes/no, true/false, 1/0, etc.

    Args:
        text: Response text
        default: Default value if unable to parse

    Returns:
        Boolean value or default
    """
    text = text.lower().strip()

    # Direct matches
    if text in ('yes', 'true', '1', 'correct', 'affirmative', 'y'):
        return True
    if text in ('no', 'false', '0', 'incorrect', 'negative', 'n'):
        return False

    # Check for keywords
    if 'yes' in text or 'true' in text or 'correct' in text:
        return True
    if 'no' in text or 'false' in text or 'incorrect' in text:
        return False

    # Try JSON parsing
    json_data = extract_json(text)
    if json_data:
        # Look for common boolean fields
        for key in ['answer', 'result', 'is_vulnerable', 'vulnerable', 'valid', 'success']:
            if key in json_data:
                return bool(json_data[key])

    logger.warning(f"Could not parse boolean from: {text[:100]}...")
    return default


def parse_confidence_score(text: str, default: float = 0.5) -> float:
    """
    Extract confidence score (0.0-1.0) from text.

    Args:
        text: Response text
        default: Default value if unable to parse

    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Try JSON parsing first
    json_data = extract_json(text)
    if json_data:
        # If it's a dict, look for confidence keys
        if isinstance(json_data, dict):
            for key in ['confidence', 'score', 'probability']:
                if key in json_data:
                    try:
                        score = float(json_data[key])
                        # Normalize to 0-1 if needed
                        if score > 1.0:
                            score = score / 100.0
                        return max(0.0, min(1.0, score))
                    except (ValueError, TypeError):
                        pass
        # If it's a number directly, use it
        elif isinstance(json_data, (int, float)):
            score = float(json_data)
            if score > 1.0:
                score = score / 100.0
            return max(0.0, min(1.0, score))

    # Look for percentages: 85%, 0.85
    percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
    match = re.search(percentage_pattern, text)
    if match:
        value = float(match.group(1))
        return max(0.0, min(1.0, value / 100.0))

    # Look for decimal: 0.85, 0.9
    decimal_pattern = r'\b0\.\d+\b'
    match = re.search(decimal_pattern, text)
    if match:
        return float(match.group(0))

    # Look for "confidence: X" or "score: X"
    score_pattern = r'(?:confidence|score|probability):\s*(\d+(?:\.\d+)?)'
    match = re.search(score_pattern, text, re.IGNORECASE)
    if match:
        value = float(match.group(1))
        if value > 1.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))

    logger.warning(f"Could not extract confidence score from: {text[:100]}...")
    return default


def parse_classification(text: str, categories: List[str]) -> Optional[str]:
    """
    Parse classification response.

    Args:
        text: Response text
        categories: List of valid categories

    Returns:
        Matched category or None
    """
    text_lower = text.lower()

    # Direct match
    for category in categories:
        if text_lower == category.lower():
            return category

    # Check if category appears in text
    for category in categories:
        if category.lower() in text_lower:
            return category

    # Try JSON parsing
    json_data = extract_json(text)
    if json_data:
        for key in ['category', 'class', 'label', 'type']:
            if key in json_data:
                value = str(json_data[key]).lower()
                for category in categories:
                    if value == category.lower():
                        return category

    logger.warning(f"Could not parse classification from: {text[:100]}...")
    return None


# ============================================================================
# Validation
# ============================================================================

def validate_response_schema(
    data: Dict[str, Any],
    required_fields: List[str],
    optional_fields: Optional[List[str]] = None,
) -> tuple[bool, List[str]]:
    """
    Validate response data against a schema.

    Args:
        data: Response data
        required_fields: List of required field names
        optional_fields: List of optional field names

    Returns:
        Tuple of (is_valid, list_of_missing_fields)
    """
    missing = []

    for field in required_fields:
        if field not in data:
            missing.append(field)

    return len(missing) == 0, missing


# ============================================================================
# Convenience Functions
# ============================================================================

def safe_parse_json(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON with a default fallback.

    Args:
        text: Text to parse
        default: Value to return if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return parse_json_response(text, strict=False)
    except Exception as e:
        logger.warning(f"JSON parsing failed: {e}")
        return default


def extract_first_sentence(text: str) -> str:
    """
    Extract first sentence from text.

    Args:
        text: Text

    Returns:
        First sentence
    """
    match = re.match(r'^([^.!?]+[.!?])', text.strip())
    if match:
        return match.group(1).strip()
    return text.strip()
