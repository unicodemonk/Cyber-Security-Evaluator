# LLM Integration Documentation

Complete documentation for the LLM integration package.

## 📚 Documentation Index

### Quick Start
- **[Package README](../README.md)** - Quick start and basic usage
- **[Examples](../examples/llm_usage_examples.py)** - 9 working code examples

### Complete Documentation
- **[Complete Guide (GUIDE.md)](GUIDE.md)** - Comprehensive guide covering:
  - Setup and configuration
  - Prompt management
  - Making requests
  - Response parsing
  - Error handling
  - Best practices
  - Cost management
  - Testing
  - Troubleshooting

- **[Summary (SUMMARY.md)](SUMMARY.md)** - Overview of what was built:
  - Feature list
  - Architecture overview
  - File structure
  - Statistics
  - Usage patterns

## 🎯 Where to Start

**New user?** Start here:
1. Read [../README.md](../README.md) for quick start
2. Look at [../examples/llm_usage_examples.py](../examples/llm_usage_examples.py) for working code
3. Reference [GUIDE.md](GUIDE.md) for details

**Ready to use?**
1. Copy `.env.example` to `.env` and add your API key
2. `pip install openai pyyaml pydantic python-dotenv`
3. Run examples: `python llm/examples/llm_usage_examples.py`

## 📖 Document Descriptions

### GUIDE.md (~800 lines)
Complete technical guide with:
- Configuration options
- Prompt template syntax (placeholders, lists, conditionals)
- LLM client features (retries, caching, cost tracking)
- Response parsing utilities
- Error handling patterns
- Best practices
- Performance optimization
- Troubleshooting

### SUMMARY.md
Quick overview showing:
- What was implemented
- Features and statistics
- File structure
- Usage patterns
- Quick reference

## 🧪 Testing

All tests are in `../../tests/test_llm_integration.py`:
```bash
pytest tests/test_llm_integration.py -v
# 36 passed ✅
```

## 🔗 Related Files

```
llm/
├── docs/
│   ├── README.md     ← You are here
│   ├── GUIDE.md      ← Complete technical guide
│   └── SUMMARY.md    ← Quick overview
├── examples/
│   └── llm_usage_examples.py  ← Working code examples
├── client.py         ← LLM client implementation
├── prompt_manager.py ← Prompt management
├── response_parser.py ← Response utilities
├── prompts.yaml      ← Prompt templates
└── README.md         ← Package quick start
```

## 💡 Need Help?

1. Check [GUIDE.md](GUIDE.md) - comprehensive reference
2. Look at [examples](../examples/llm_usage_examples.py) - working code
3. See [SUMMARY.md](SUMMARY.md) - quick overview
4. Run tests - verify everything works

## 🚀 Quick Reference

**Initialize:**
```python
from llm import LLMClient, PromptManager

client = LLMClient()
manager = PromptManager("llm/prompts.yaml")
```

**Use prompt:**
```python
rendered = manager.render("analyze_sql_injection", {
    "code": "...",
    "language": "python",
    "category": "classic_sqli"
})

response = client.generate(
    prompt=rendered.user_prompt,
    system_prompt=rendered.system_prompt,
    response_format=rendered.response_format
)
```

For details, see [GUIDE.md](GUIDE.md).
