"""
LLM Integration Package

Provides a complete LLM integration system with:
- OpenAI client wrapper with error handling and retries
- Prompt management with YAML repository
- Dynamic placeholder replacement
- Response parsing utilities
- Caching and cost tracking

Usage:
    from llm import LLMClient, PromptManager

    # Initialize client
    client = LLMClient()

    # Load prompt manager
    manager = PromptManager("config/prompts.yaml")

    # Render and execute prompt
    rendered = manager.render("analyze_sql_injection", {
        "code": "SELECT * FROM users WHERE id=" + user_id,
        "language": "python",
        "category": "classic_sqli"
    })

    # Call LLM
    response = client.generate(
        prompt=rendered.user_prompt,
        system_prompt=rendered.system_prompt,
        response_format=rendered.response_format,
    )

    print(response.content)
"""

from .client import (
    LLMClient,
    LLMRequest,
    LLMResponse,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)

from .prompt_manager import (
    PromptManager,
    PromptTemplate,
    RenderedPrompt,
    PromptRenderer,
    load_prompt_manager,
)

from .response_parser import (
    extract_json,
    parse_json_response,
    extract_code_blocks,
    extract_list_items,
    extract_key_value_pairs,
    parse_boolean_response,
    parse_confidence_score,
    parse_classification,
    validate_response_schema,
    safe_parse_json,
)


__all__ = [
    # Client
    "LLMClient",
    "LLMRequest",
    "LLMResponse",
    "LLMError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMValidationError",
    # Prompt Management
    "PromptManager",
    "PromptTemplate",
    "RenderedPrompt",
    "PromptRenderer",
    "load_prompt_manager",
    # Response Parsing
    "extract_json",
    "parse_json_response",
    "extract_code_blocks",
    "extract_list_items",
    "extract_key_value_pairs",
    "parse_boolean_response",
    "parse_confidence_score",
    "parse_classification",
    "validate_response_schema",
    "safe_parse_json",
]


__version__ = "1.0.0"
