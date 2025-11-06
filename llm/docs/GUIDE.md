# LLM Integration Guide

Complete guide for using the LLM integration system with OpenAI and other providers.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Prompt Management](#prompt-management)
5. [Making Requests](#making-requests)
6. [Response Parsing](#response-parsing)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Cost Management](#cost-management)
10. [Testing](#testing)

---

## 🚀 Quick Start

### 1. Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
nano .env  # or your preferred editor

# Install dependencies
pip install openai pyyaml pydantic python-dotenv
```

### 2. Basic Usage

```python
from llm import LLMClient, PromptManager

# Initialize
client = LLMClient()
manager = PromptManager("config/prompts.yaml")

# Render prompt
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

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Application                     │
└─────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  LLM Integration Layer                  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │    Prompt    │  │  LLM Client  │  │   Response   │ │
│  │   Manager    │  │              │  │    Parser    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 OpenAI / Anthropic / etc.               │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **LLMClient**: Handles API calls with retry, caching, and error handling
2. **PromptManager**: Loads and renders prompts from YAML repository
3. **ResponseParser**: Extracts structured data from responses

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx

# Optional (with defaults)
OPENAI_MODEL=gpt-4o-mini              # Model to use
OPENAI_TEMPERATURE=0.7                # Sampling temperature
OPENAI_MAX_TOKENS=2000                # Max tokens to generate
OPENAI_TIMEOUT=30                     # Request timeout (seconds)

# Retry configuration
LLM_RETRY_ATTEMPTS=3                  # Max retry attempts
LLM_RETRY_DELAY=2                     # Base retry delay (seconds)

# Caching
LLM_CACHE_ENABLED=true                # Enable response caching
LLM_CACHE_TTL=3600                    # Cache TTL (seconds)

# Logging
LLM_LOG_REQUESTS=true                 # Log requests
LLM_LOG_RESPONSES=true                # Log responses
LLM_LOG_LEVEL=INFO                    # Log level
```

### Client Configuration

```python
client = LLMClient(
    api_key="sk-...",              # Or from env
    model="gpt-4o-mini",           # Default model
    temperature=0.7,               # Default temperature
    max_tokens=2000,               # Default max tokens
    timeout=30,                    # Request timeout
    max_retries=3,                 # Retry attempts
    retry_delay=2.0,               # Base retry delay
    enable_cache=True,             # Enable caching
    cache_ttl=3600,                # Cache TTL
)
```

---

## 📝 Prompt Management

### Prompt Structure (YAML)

```yaml
prompt_key:
  system: |
    System prompt here. Optional.

  user: |
    User prompt with {{placeholders}}.

    Lists:
    {{#items}}
    - {{.}}
    {{/items}}

    Conditionals:
    {{#show_details}}
    Additional details: {{details}}
    {{/show_details}}

  placeholders:
    - required_field_1
    - required_field_2

  response_format: json  # or text, json_object
  temperature: 0.3       # Optional override
  max_tokens: 1000       # Optional override

  metadata:
    domain: security
    requires_expertise: true
```

### Placeholder Types

#### 1. Simple Placeholders

```yaml
user: "Analyze this {{language}} code: {{code}}"
```

```python
manager.render("prompt_key", {
    "language": "python",
    "code": "print('hello')"
})
# Output: "Analyze this python code: print('hello')"
```

#### 2. List Iteration

```yaml
user: |
  Requirements:
  {{#requirements}}
  - {{.}}
  {{/requirements}}
```

```python
manager.render("prompt_key", {
    "requirements": ["Security", "Performance", "Readability"]
})
# Output:
# Requirements:
# - Security
# - Performance
# - Readability
```

#### 3. Complex List Items

```yaml
user: |
  {{#tests}}
  Test {{id}}: {{description}}
  Expected: {{expected}}

  {{/tests}}
```

```python
manager.render("prompt_key", {
    "tests": [
        {"id": 1, "description": "Check auth", "expected": "pass"},
        {"id": 2, "description": "Validate input", "expected": "pass"},
    ]
})
```

#### 4. Conditional Blocks

```yaml
user: |
  Analyze code.

  {{#include_examples}}
  Here are some examples:
  {{examples}}
  {{/include_examples}}
```

```python
# With examples
manager.render("prompt_key", {
    "include_examples": True,
    "examples": "Example 1: ..."
})

# Without examples
manager.render("prompt_key", {
    "include_examples": False,
    "examples": "Example 1: ..."
})
# The {{#include_examples}} block won't appear
```

---

## 🔧 Making Requests

### Basic Request

```python
response = client.generate(
    prompt="What is SQL injection?",
    max_tokens=100,
)
print(response.content)
```

### With System Prompt

```python
response = client.generate(
    system_prompt="You are a security expert.",
    prompt="Explain SQL injection.",
)
```

### JSON Response

```python
# Method 1: Using generate()
response = client.generate(
    prompt="Classify this: 'SQL injection vulnerability'",
    response_format="json_object",
)
data = json.loads(response.content)

# Method 2: Using generate_json()
data = client.generate_json(
    prompt="Return JSON with fields: category, severity",
)
print(data["category"])
```

### Using Prompt Manager

```python
# Render prompt
rendered = manager.render("analyze_code", {
    "code": "...",
    "language": "python",
})

# Call LLM
response = client.generate(
    prompt=rendered.user_prompt,
    system_prompt=rendered.system_prompt,
    response_format=rendered.response_format,
    temperature=rendered.temperature,
    max_tokens=rendered.max_tokens,
)
```

### Shortcuts

```python
# Quick way to render and call
prompt_params = manager.render_to_dict("analyze_code", {...})
response = client.generate(**prompt_params)
```

---

## 🔍 Response Parsing

### Parse JSON

```python
from llm import parse_json_response, extract_json

# Extract JSON from messy response
data = extract_json(response.content)

# Parse and validate with Pydantic
from pydantic import BaseModel

class Analysis(BaseModel):
    is_vulnerable: bool
    confidence: float
    explanation: str

analysis = parse_json_response(
    response.content,
    model=Analysis,
    strict=True  # Raise error if invalid
)
```

### Extract Structured Data

```python
from llm import (
    extract_code_blocks,
    extract_list_items,
    extract_key_value_pairs,
)

# Extract code blocks
code = extract_code_blocks(response.content, language="python")

# Extract lists
items = extract_list_items(response.content, numbered=True, bulleted=True)

# Extract key-value pairs
pairs = extract_key_value_pairs(response.content)
# Returns: {"Key1": "Value1", "Key2": "Value2", ...}
```

### Parse Boolean/Confidence

```python
from llm import parse_boolean_response, parse_confidence_score

# Parse yes/no, true/false, etc.
is_vulnerable = parse_boolean_response(response.content)

# Extract confidence score (0.0-1.0)
confidence = parse_confidence_score(response.content)
```

---

## ⚠️ Error Handling

### Exception Hierarchy

```
LLMError (base)
├── LLMRateLimitError (retryable)
├── LLMTimeoutError (retryable)
└── LLMValidationError (not retryable)
```

### Handling Errors

```python
from llm import (
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)

try:
    response = client.generate(prompt="...")

except LLMRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
    # Wait and retry manually, or client will retry automatically

except LLMTimeoutError as e:
    print(f"Timeout: {e}")
    # Reduce prompt size or increase timeout

except LLMValidationError as e:
    print(f"Validation failed: {e}")
    # Fix prompt or request parameters

except LLMError as e:
    print(f"General LLM error: {e}")
    if e.retryable:
        # Can retry
        pass
```

### Automatic Retries

The client automatically retries on:
- Rate limit errors (with exponential backoff)
- Connection/timeout errors
- Server errors (500, 502, 503, 504)

```python
client = LLMClient(
    max_retries=3,      # Max 3 retry attempts
    retry_delay=2.0,    # Start with 2s delay, doubles each retry
)

# Retries happen automatically
response = client.generate(...)
```

---

## ✨ Best Practices

### 1. Prompt Design

✅ **Good:**
```yaml
analyze_code:
  system: |
    You are a security expert. Analyze code for vulnerabilities.
    Be concise and specific.

  user: |
    Analyze this {{language}} code:
    ```{{language}}
    {{code}}
    ```

    Category: {{category}}

    Return JSON with: is_vulnerable (bool), confidence (0-1), explanation (string)
```

❌ **Bad:**
```yaml
analyze_code:
  user: |
    Here's some code {{code}} in {{language}} maybe check if it has
    issues? Return whatever format you want.
```

**Why:**
- Clear instructions
- Structured format
- Specific output requirements
- Examples help

### 2. Temperature Settings

- **0.0-0.3**: Factual, deterministic tasks (analysis, classification)
- **0.4-0.7**: Balanced creativity (explanations, code generation)
- **0.8-1.0**: Creative tasks (brainstorming, stories)
- **> 1.0**: Very random (rarely useful)

```python
# For security analysis - be deterministic
response = client.generate(prompt="...", temperature=0.2)

# For code explanations - balanced
response = client.generate(prompt="...", temperature=0.5)
```

### 3. Token Management

```python
# Estimate tokens (rough: 1 token ≈ 4 chars)
prompt_tokens = len(prompt) // 4

# Set appropriate max_tokens
if prompt_tokens < 500:
    max_tokens = 1000
else:
    max_tokens = 2000

response = client.generate(prompt=prompt, max_tokens=max_tokens)
```

### 4. Caching Strategy

```python
# Cache expensive, repeated queries
client = LLMClient(enable_cache=True, cache_ttl=3600)

# Disable cache for dynamic content
response = client.generate(prompt="...", use_cache=False)

# Clear cache when needed
client.clear_cache()
```

### 5. Error Recovery

```python
def safe_llm_call(prompt, max_attempts=3):
    """Robust LLM call with fallback."""
    for attempt in range(max_attempts):
        try:
            return client.generate(prompt=prompt)
        except LLMRateLimitError as e:
            if attempt < max_attempts - 1:
                time.sleep(e.retry_after or 5)
            else:
                raise
        except LLMError as e:
            if not e.retryable:
                raise
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
            else:
                raise
```

### 6. Structured Outputs

Always use JSON for structured data:

```python
# ✅ Request JSON explicitly
response = client.generate_json(
    system_prompt="Return JSON only.",
    prompt="Analyze and return: {category, severity, description}",
)

# ❌ Don't rely on free-form text
response = client.generate(
    prompt="Analyze this and tell me the category and severity",
)
```

### 7. Prompt Versioning

```yaml
# Old version (keep for compatibility)
analyze_code_v1:
  user: "Analyze: {{code}}"

# New improved version
analyze_code_v2:
  system: "You are a security expert..."
  user: "Analyze this {{language}} code:\n{{code}}\n\nCategory: {{category}}"
  response_format: json

# Use versioning in your code
analyze_code:  # Always points to latest
  $ref: analyze_code_v2
```

---

## 💰 Cost Management

### Track Costs

```python
# Initialize with tracking
client = LLMClient(model="gpt-4o-mini")

# Make requests
for task in tasks:
    response = client.generate(...)

# Get stats
stats = client.get_stats()
print(f"Total cost: ${stats['total_cost_usd']:.6f}")
print(f"Avg cost per request: ${stats['avg_cost_per_request']:.6f}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Cache hit rate: {stats['cache_hit_rate']*100:.1f}%")
```

### Cost Optimization

1. **Use cheaper models** when possible
   ```python
   # For simple tasks
   client = LLMClient(model="gpt-4o-mini")  # Cheaper

   # For complex reasoning
   client = LLMClient(model="gpt-4o")  # More expensive
   ```

2. **Enable caching**
   ```python
   client = LLMClient(enable_cache=True, cache_ttl=7200)
   ```

3. **Reduce token usage**
   - Use concise prompts
   - Set appropriate `max_tokens`
   - Use stop sequences if applicable

4. **Batch similar requests**
   ```python
   # Instead of individual calls
   prompts = ["Analyze X", "Analyze Y", "Analyze Z"]
   for p in prompts:
       client.generate(p)

   # Combine into one call
   combined = "\n\n".join(f"{i}. {p}" for i, p in enumerate(prompts, 1))
   client.generate(combined)
   ```

### Pricing (as of 2024)

| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|-------|---------------------|----------------------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |

---

## 🧪 Testing

### Unit Tests

```python
import pytest
from llm import LLMClient, PromptManager

def test_prompt_rendering():
    manager = PromptManager("config/prompts.yaml")
    rendered = manager.render("test_prompt", {
        "var1": "value1",
        "var2": "value2",
    })
    assert "value1" in rendered.user_prompt
    assert "value2" in rendered.user_prompt

def test_client_caching():
    client = LLMClient(enable_cache=True)
    response1 = client.generate("Test prompt")
    response2 = client.generate("Test prompt")
    assert response2.cached == True

def test_error_handling():
    client = LLMClient(api_key="invalid")
    with pytest.raises(LLMError):
        client.generate("Test")
```

### Integration Tests

```python
def test_full_workflow():
    """Test complete workflow."""
    client = LLMClient()
    manager = PromptManager("config/prompts.yaml")

    # Render
    rendered = manager.render("analyze_sql_injection", {
        "code": "SELECT * FROM users",
        "language": "sql",
        "category": "test"
    })

    # Call LLM
    response = client.generate(
        prompt=rendered.user_prompt,
        system_prompt=rendered.system_prompt,
    )

    # Validate
    assert response.content
    assert response.usage["total_tokens"] > 0
    assert response.cost_usd is not None
```

---

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 🔍 Troubleshooting

### API Key Not Found
```
ValueError: OpenAI API key not provided
```
**Solution:** Set `OPENAI_API_KEY` in `.env` file

### Rate Limit Errors
```
LLMRateLimitError: Rate limit exceeded
```
**Solution:**
- Increase `retry_delay`
- Add delays between requests
- Upgrade API tier

### JSON Parsing Fails
```
LLMValidationError: Expected JSON response but got invalid JSON
```
**Solution:**
- Use `response_format="json_object"`
- Add "Return valid JSON only" to prompt
- Use `parse_json_response()` with `strict=False`

### Timeouts
```
LLMTimeoutError: Request failed after 3 attempts
```
**Solution:**
- Increase `timeout` parameter
- Reduce prompt size
- Check network connection

---

**Questions? Check `examples/llm_usage_examples.py` for working code!**
