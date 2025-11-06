# LLM Integration Package

Production-ready LLM integration with OpenAI, featuring prompt management, error handling, caching, and response parsing.

## Quick Start

```python
from llm import LLMClient, PromptManager

# Initialize
client = LLMClient()
manager = PromptManager("config/prompts.yaml")

# Use a prompt
rendered = manager.render("analyze_sql_injection", {
    "code": "SELECT * FROM users WHERE id=" + user_id,
    "language": "python",
    "category": "classic_sqli"
})

# Call LLM
response = client.generate(
    prompt=rendered.user_prompt,
    system_prompt=rendered.system_prompt,
    response_format=rendered.response_format
)

print(response.content)
```

## Features

- ✅ **Error Handling**: Automatic retries, rate limit handling, timeout management
- ✅ **Caching**: In-memory cache with TTL to reduce costs
- ✅ **Cost Tracking**: Token usage and cost estimation
- ✅ **Prompt Management**: YAML-based prompts with dynamic placeholders
- ✅ **Response Parsing**: JSON extraction, boolean parsing, structured data
- ✅ **Best Practices**: Logging, validation, type hints, comprehensive tests

## Components

### 1. LLMClient (`client.py`)
OpenAI API wrapper with enterprise features.

**Key Methods:**
- `generate()` - Generate text response
- `generate_json()` - Generate and parse JSON
- `get_stats()` - Get usage statistics
- `clear_cache()` - Clear response cache

### 2. PromptManager (`prompt_manager.py`)
Load and render prompts from YAML files.

**Key Methods:**
- `render()` - Render prompt with context
- `list_prompts()` - List available prompts
- `get_template()` - Get prompt template

### 3. ResponseParser (`response_parser.py`)
Parse and validate LLM responses.

**Key Functions:**
- `extract_json()` - Extract JSON from text
- `parse_boolean_response()` - Parse yes/no responses
- `parse_confidence_score()` - Extract confidence (0.0-1.0)
- `extract_code_blocks()` - Extract code by language

## Installation

```bash
pip install openai pyyaml pydantic python-dotenv
```

## Configuration

Create `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
```

## Documentation

- **Complete Guide**: `docs/GUIDE.md`
- **Summary**: `docs/SUMMARY.md`
- **Examples**: `examples/llm_usage_examples.py`
- **Tests**: `../tests/test_llm_integration.py`

## Tests

Run tests:
```bash
pytest tests/test_llm_integration.py -v
# 36 passed in 0.35s ✅
```

## Examples

See `llm/examples/llm_usage_examples.py` for 9 comprehensive examples covering all features.

```bash
# Run examples
python llm/examples/llm_usage_examples.py
```
