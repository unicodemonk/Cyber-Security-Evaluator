"""
LLM Integration Usage Examples

This file demonstrates how to use the LLM integration system with various scenarios.
"""

import os
import sys

# Add parent directory to path (llm package is parent of examples)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from llm import (
    LLMClient,
    PromptManager,
    parse_json_response,
    parse_boolean_response,
    parse_confidence_score,
)

# Get path to prompts.yaml (in llm/ directory)
PROMPTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts.yaml")


# ============================================================================
# Example 1: Basic Usage
# ============================================================================

def example_basic_usage():
    """Basic usage of LLM client."""
    print("\n" + "="*70)
    print("Example 1: Basic Usage")
    print("="*70 + "\n")

    # Initialize client
    client = LLMClient(
        model="gpt-4o-mini",
        temperature=0.7,
        enable_cache=True,
    )

    # Simple prompt
    response = client.generate(
        prompt="Explain SQL injection in one sentence.",
        temperature=0.5,
        max_tokens=100,
    )

    print(f"Response: {response.content}")
    print(f"Tokens used: {response.usage['total_tokens']}")
    print(f"Cost: ${response.cost_usd:.6f}")
    print(f"Latency: {response.latency_ms:.2f}ms")
    print(f"Cached: {response.cached}")

    # Same request again (should be cached)
    print("\n--- Calling again (should hit cache) ---\n")
    response2 = client.generate(
        prompt="Explain SQL injection in one sentence.",
        temperature=0.5,
        max_tokens=100,
    )
    print(f"Cached: {response2.cached}")
    print(f"Latency: {response2.latency_ms:.2f}ms")

    # Get stats
    print(f"\n--- Client Stats ---")
    print(client.get_stats())


# ============================================================================
# Example 2: Using Prompt Manager
# ============================================================================

def example_prompt_manager():
    """Using prompt manager with YAML prompts."""
    print("\n" + "="*70)
    print("Example 2: Prompt Manager")
    print("="*70 + "\n")

    # Initialize
    client = LLMClient()
    manager = PromptManager(PROMPTS_PATH)

    print(f"Available prompts: {', '.join(manager.list_prompts())}\n")

    # Render a prompt
    rendered = manager.render("analyze_sql_injection", {
        "code": 'query = f"SELECT * FROM users WHERE id={user_id}"',
        "language": "python",
        "category": "classic_sqli",
    })

    print(f"System Prompt:\n{rendered.system_prompt}\n")
    print(f"User Prompt:\n{rendered.user_prompt}\n")

    # Call LLM
    response = client.generate(
        prompt=rendered.user_prompt,
        system_prompt=rendered.system_prompt,
        response_format=rendered.response_format,
        temperature=rendered.temperature,
        max_tokens=rendered.max_tokens,
    )

    print(f"Response:\n{response.content}\n")


# ============================================================================
# Example 3: JSON Response
# ============================================================================

def example_json_response():
    """Getting structured JSON responses."""
    print("\n" + "="*70)
    print("Example 3: JSON Response")
    print("="*70 + "\n")

    client = LLMClient()
    manager = PromptManager(PROMPTS_PATH)

    # Render prompt for classification
    rendered = manager.render("classify_text", {
        "text": "This code has a SQL injection vulnerability due to string concatenation.",
        "categories": "security_issue, code_quality, performance, documentation",
    })

    # Get JSON response
    result = client.generate_json(
        prompt=rendered.user_prompt,
        system_prompt=rendered.system_prompt,
    )

    print(f"JSON Result:")
    print(f"  Category: {result.get('category')}")
    print(f"  Confidence: {result.get('confidence')}")
    print(f"  Reasoning: {result.get('reasoning')}\n")


# ============================================================================
# Example 4: List Iteration in Prompts
# ============================================================================

def example_list_iteration():
    """Using lists in prompt templates."""
    print("\n" + "="*70)
    print("Example 4: List Iteration")
    print("="*70 + "\n")

    client = LLMClient()
    manager = PromptManager(PROMPTS_PATH)

    # Render with list data
    rendered = manager.render("evaluate_code_quality", {
        "code": """
def get_user(id):
    return db.query("SELECT * FROM users WHERE id=" + str(id))
        """,
        "language": "python",
        "focus_areas": ["security", "error_handling", "code_style"],
    })

    print(f"Rendered Prompt:\n{rendered.user_prompt}\n")

    response = client.generate_json(
        prompt=rendered.user_prompt,
        system_prompt=rendered.system_prompt,
    )

    print(f"Quality Evaluation:")
    for area, score in response.items():
        print(f"  {area}: {score}")


# ============================================================================
# Example 5: Conditional Blocks
# ============================================================================

def example_conditional_blocks():
    """Using conditional blocks in prompts."""
    print("\n" + "="*70)
    print("Example 5: Conditional Blocks")
    print("="*70 + "\n")

    manager = PromptManager(PROMPTS_PATH)

    # With remediation
    print("--- With Remediation ---\n")
    rendered1 = manager.render("explain_vulnerability", {
        "vulnerability_type": "SQL Injection",
        "code": 'query = "SELECT * FROM users WHERE id=" + user_id',
        "language": "python",
        "level": "beginner",
        "include_remediation": True,
        "include_examples": False,
    })
    print(rendered1.user_prompt[:300] + "...\n")

    # Without remediation
    print("--- Without Remediation ---\n")
    rendered2 = manager.render("explain_vulnerability", {
        "vulnerability_type": "SQL Injection",
        "code": 'query = "SELECT * FROM users WHERE id=" + user_id',
        "language": "python",
        "level": "beginner",
        "include_remediation": False,
        "include_examples": True,
    })
    print(rendered2.user_prompt[:300] + "...\n")


# ============================================================================
# Example 6: Response Parsing
# ============================================================================

def example_response_parsing():
    """Parsing various response formats."""
    print("\n" + "="*70)
    print("Example 6: Response Parsing")
    print("="*70 + "\n")

    # Boolean parsing
    print("--- Boolean Parsing ---")
    responses = [
        "Yes, this code is vulnerable.",
        "No",
        '{"is_vulnerable": true, "confidence": 0.95}',
    ]
    for resp in responses:
        result = parse_boolean_response(resp)
        print(f"  '{resp[:40]}...' -> {result}")

    print("\n--- Confidence Parsing ---")
    confidence_responses = [
        "Confidence: 85%",
        "Score: 0.92",
        '{"confidence": 0.88}',
    ]
    for resp in confidence_responses:
        score = parse_confidence_score(resp)
        print(f"  '{resp}' -> {score:.2f}")


# ============================================================================
# Example 7: Error Handling
# ============================================================================

def example_error_handling():
    """Demonstrating error handling."""
    print("\n" + "="*70)
    print("Example 7: Error Handling")
    print("="*70 + "\n")

    from llm import LLMError, LLMRateLimitError, LLMTimeoutError

    client = LLMClient(max_retries=2, timeout=5)

    try:
        # This will work
        response = client.generate("What is 2+2?", max_tokens=10)
        print(f"Success: {response.content}")

    except LLMRateLimitError as e:
        print(f"Rate limit exceeded. Retry after {e.retry_after}s")

    except LLMTimeoutError as e:
        print(f"Request timed out: {e}")

    except LLMError as e:
        print(f"LLM error: {e}")
        if e.retryable:
            print("  (This error is retryable)")


# ============================================================================
# Example 8: Cost Tracking
# ============================================================================

def example_cost_tracking():
    """Tracking API costs."""
    print("\n" + "="*70)
    print("Example 8: Cost Tracking")
    print("="*70 + "\n")

    client = LLMClient(model="gpt-4o-mini")

    # Make several requests
    prompts = [
        "What is SQL injection?",
        "Explain XSS attacks.",
        "What is CSRF?",
    ]

    for prompt in prompts:
        response = client.generate(prompt, max_tokens=50)
        print(f"Prompt: {prompt}")
        print(f"  Tokens: {response.usage['total_tokens']}, Cost: ${response.cost_usd:.6f}")

    print(f"\n--- Total Stats ---")
    stats = client.get_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Total cost: ${stats['total_cost_usd']:.6f}")
    print(f"Avg cost per request: ${stats['avg_cost_per_request']:.6f}")
    print(f"Cache hit rate: {stats['cache_hit_rate']*100:.1f}%")


# ============================================================================
# Example 9: Complex Nested Data
# ============================================================================

def example_complex_nested_data():
    """Using complex nested data structures in prompts."""
    print("\n" + "="*70)
    print("Example 9: Complex Nested Data")
    print("="*70 + "\n")

    manager = PromptManager(PROMPTS_PATH)

    # Debate judging with nested data
    rendered = manager.render("judge_debate", {
        "topic": "Should AI be regulated?",
        "pro_arguments": [
            {"round": 1, "argument": "AI poses existential risks that require oversight."},
            {"round": 2, "argument": "Regulation prevents misuse and protects privacy."},
            {"round": 3, "argument": "Historical precedent shows regulation drives innovation."},
        ],
        "con_arguments": [
            {"round": 1, "argument": "Innovation requires freedom from restrictive rules."},
            {"round": 2, "argument": "Self-regulation is more effective than government control."},
            {"round": 3, "argument": "Premature regulation stifles technological progress."},
        ],
    })

    print("Rendered Prompt:")
    print(rendered.user_prompt)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("LLM Integration - Usage Examples")
    print("="*70)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set!")
        print("Set your API key in .env file or as environment variable.\n")
        print("For testing, you can still run examples that don't call the API:")
        print("  - example_conditional_blocks()")
        print("  - example_response_parsing()")
        print("  - example_complex_nested_data()")
        sys.exit(1)

    # Run examples (comment out to skip)
    try:
        example_basic_usage()
        example_prompt_manager()
        example_json_response()
        example_list_iteration()
        example_conditional_blocks()
        example_response_parsing()
        example_error_handling()
        example_cost_tracking()
        example_complex_nested_data()

        print("\n" + "="*70)
        print("✅ All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
