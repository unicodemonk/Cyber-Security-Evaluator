"""
Prompt Manager for loading and rendering prompts with dynamic placeholders.

Supports:
- YAML-based prompt repository
- Dynamic placeholder replacement
- Mustache-style templating for lists and conditionals
- Validation of required placeholders
- Prompt versioning and metadata
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================

class PromptTemplate(BaseModel):
    """A prompt template with metadata."""

    key: str = Field(..., description="Unique identifier for the prompt")
    system: Optional[str] = Field(None, description="System prompt")
    user: str = Field(..., description="User prompt template")
    placeholders: List[str] = Field(default_factory=list, description="Required placeholder names")
    response_format: str = Field("text", description="Expected response format")
    temperature: Optional[float] = Field(None, description="Override temperature")
    max_tokens: Optional[int] = Field(None, description="Override max_tokens")
    examples: Optional[List[Dict[str, str]]] = Field(None, description="Few-shot examples")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('response_format')
    @classmethod
    def validate_response_format(cls, v: str) -> str:
        """Validate response format."""
        valid_formats = {"text", "json", "json_object"}
        if v not in valid_formats:
            raise ValueError(f"response_format must be one of {valid_formats}, got: {v}")
        return v


class RenderedPrompt(BaseModel):
    """A rendered prompt ready for LLM."""

    system_prompt: Optional[str] = Field(None, description="Rendered system prompt")
    user_prompt: str = Field(..., description="Rendered user prompt")
    response_format: str = Field("text", description="Expected response format")
    temperature: Optional[float] = Field(None, description="Temperature override")
    max_tokens: Optional[int] = Field(None, description="Max tokens override")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


# ============================================================================
# Prompt Renderer
# ============================================================================

class PromptRenderer:
    """
    Renders prompt templates with placeholders.

    Supports:
    - Simple placeholders: {{variable}}
    - List iteration: {{#list}} ... {{/list}}
    - Conditionals: {{#if_var}} ... {{/if_var}}
    - Dot notation for list items: {{.}}
    """

    @staticmethod
    def render(template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template: Template string with placeholders
            context: Dictionary of values to substitute

        Returns:
            Rendered string

        Examples:
            >>> render("Hello {{name}}!", {"name": "World"})
            'Hello World!'

            >>> render("Items: {{#items}}\\n- {{.}}{{/items}}", {"items": ["a", "b"]})
            'Items: \\n- a\\n- b'
        """
        # Handle list iterations and conditionals
        template = PromptRenderer._render_blocks(template, context)

        # Handle simple placeholders
        template = PromptRenderer._render_placeholders(template, context)

        return template

    @staticmethod
    def _render_blocks(template: str, context: Dict[str, Any]) -> str:
        """Render block expressions (lists and conditionals)."""

        # Pattern: {{#key}} ... {{/key}}
        block_pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

        def replace_block(match):
            key = match.group(1)
            block_template = match.group(2)

            value = context.get(key)

            # If value is a list, iterate
            if isinstance(value, list):
                if not value:
                    return ""  # Empty list
                return "".join(
                    PromptRenderer._render_list_item(block_template, item, context)
                    for item in value
                )

            # If value is truthy, render the block once
            elif value:
                return PromptRenderer._render_placeholders(block_template, context)

            # If value is falsy, don't render
            else:
                return ""

        # Recursively replace blocks (for nested blocks)
        prev_template = None
        while prev_template != template:
            prev_template = template
            template = re.sub(block_pattern, replace_block, template, flags=re.DOTALL)

        return template

    @staticmethod
    def _render_list_item(template: str, item: Any, context: Dict[str, Any]) -> str:
        """Render a template for a single list item."""
        # Create new context with item
        item_context = context.copy()

        if isinstance(item, dict):
            # If item is a dict, merge it into context
            item_context.update(item)
        else:
            # If item is a simple value, make it available as {{.}}
            item_context['.'] = str(item)

        return PromptRenderer._render_placeholders(template, item_context)

    @staticmethod
    def _render_placeholders(template: str, context: Dict[str, Any]) -> str:
        """Render simple {{placeholder}} expressions."""

        def replace_placeholder(match):
            key = match.group(1)
            value = context.get(key, '')

            # Convert to string
            if value is None:
                return ''
            elif isinstance(value, bool):
                return str(value).lower()
            elif isinstance(value, (list, dict)):
                # Don't render complex types as simple placeholders
                logger.warning(f"Placeholder '{key}' is a {type(value).__name__}, use block syntax instead")
                return ''
            else:
                return str(value)

        return re.sub(r'\{\{(\w+|\.)\}\}', replace_placeholder, template)

    @staticmethod
    def extract_placeholders(template: str) -> List[str]:
        """Extract all placeholder names from a template."""
        placeholders = set()

        # Simple placeholders: {{name}}
        simple = re.findall(r'\{\{(\w+)\}\}', template)
        placeholders.update(simple)

        # Block placeholders: {{#name}} ... {{/name}}
        blocks = re.findall(r'\{\{#(\w+)\}\}', template)
        placeholders.update(blocks)

        # Remove the special '.' placeholder
        placeholders.discard('.')

        return sorted(list(placeholders))


# ============================================================================
# Prompt Manager
# ============================================================================

class PromptManager:
    """
    Manages loading and rendering of prompts from YAML files.

    Usage:
        manager = PromptManager("config/prompts.yaml")
        prompt = manager.render("analyze_sql_injection", {
            "code": "SELECT * FROM users WHERE id=" + user_id,
            "language": "python",
            "category": "classic_sqli"
        })
    """

    def __init__(self, prompts_path: Union[str, Path]):
        """
        Initialize prompt manager.

        Args:
            prompts_path: Path to YAML file containing prompts
        """
        self.prompts_path = Path(prompts_path)
        self.templates: Dict[str, PromptTemplate] = {}
        self.renderer = PromptRenderer()

        self.load_prompts()

    def load_prompts(self):
        """Load prompts from YAML file."""
        if not self.prompts_path.exists():
            raise FileNotFoundError(f"Prompts file not found: {self.prompts_path}")

        logger.info(f"Loading prompts from: {self.prompts_path}")

        with open(self.prompts_path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"No prompts found in {self.prompts_path}")
            return

        for key, config in data.items():
            try:
                # Auto-detect placeholders if not specified
                if 'placeholders' not in config:
                    system = config.get('system', '')
                    user = config.get('user', '')
                    config['placeholders'] = self.renderer.extract_placeholders(system + user)

                template = PromptTemplate(
                    key=key,
                    system=config.get('system'),
                    user=config['user'],
                    placeholders=config.get('placeholders', []),
                    response_format=config.get('response_format', 'text'),
                    temperature=config.get('temperature'),
                    max_tokens=config.get('max_tokens'),
                    examples=config.get('examples'),
                    metadata=config.get('metadata', {}),
                )
                self.templates[key] = template

            except Exception as e:
                logger.error(f"Failed to load prompt '{key}': {e}")
                continue

        logger.info(f"Loaded {len(self.templates)} prompts")

    def list_prompts(self) -> List[str]:
        """Get list of available prompt keys."""
        return sorted(list(self.templates.keys()))

    def get_template(self, key: str) -> PromptTemplate:
        """
        Get a prompt template by key.

        Args:
            key: Prompt key

        Returns:
            PromptTemplate

        Raises:
            KeyError: If prompt key not found
        """
        if key not in self.templates:
            raise KeyError(
                f"Prompt '{key}' not found. Available prompts: {', '.join(self.list_prompts())}"
            )
        return self.templates[key]

    def validate_context(self, template: PromptTemplate, context: Dict[str, Any]) -> List[str]:
        """
        Validate that all required placeholders are present in context.

        Args:
            template: The prompt template
            context: The context dictionary

        Returns:
            List of missing placeholder names (empty if all present)
        """
        missing = []
        for placeholder in template.placeholders:
            if placeholder not in context:
                missing.append(placeholder)
        return missing

    def render(
        self,
        key: str,
        context: Dict[str, Any],
        validate: bool = True,
    ) -> RenderedPrompt:
        """
        Render a prompt with the given context.

        Args:
            key: Prompt key
            context: Dictionary of placeholder values
            validate: Whether to validate required placeholders

        Returns:
            RenderedPrompt ready for LLM

        Raises:
            KeyError: If prompt key not found
            ValueError: If required placeholders are missing (when validate=True)
        """
        template = self.get_template(key)

        # Validate context
        if validate:
            missing = self.validate_context(template, context)
            if missing:
                raise ValueError(
                    f"Missing required placeholders for prompt '{key}': {', '.join(missing)}\n"
                    f"Required: {', '.join(template.placeholders)}\n"
                    f"Provided: {', '.join(context.keys())}"
                )

        # Render system prompt
        system_prompt = None
        if template.system:
            system_prompt = self.renderer.render(template.system, context)

        # Render user prompt
        user_prompt = self.renderer.render(template.user, context)

        # Add few-shot examples if present
        if template.examples:
            examples_text = "\n\nExamples:\n"
            for i, example in enumerate(template.examples, 1):
                examples_text += f"\nExample {i}:\n"
                if 'input' in example:
                    examples_text += f"Input:\n{example['input']}\n"
                if 'output' in example:
                    examples_text += f"Output:\n{example['output']}\n"

            user_prompt += examples_text

        return RenderedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format=template.response_format,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            metadata=template.metadata,
        )

    def render_to_dict(self, key: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render a prompt and return as dictionary (useful for LLM client).

        Args:
            key: Prompt key
            context: Placeholder values

        Returns:
            Dictionary with prompt parameters
        """
        rendered = self.render(key, context)
        return {
            "prompt": rendered.user_prompt,
            "system_prompt": rendered.system_prompt,
            "response_format": rendered.response_format,
            "temperature": rendered.temperature,
            "max_tokens": rendered.max_tokens,
            "metadata": rendered.metadata,
        }


# ============================================================================
# Utility Functions
# ============================================================================

def load_prompt_manager(prompts_path: Optional[str] = None) -> PromptManager:
    """
    Load prompt manager with default path.

    Args:
        prompts_path: Path to prompts YAML file (defaults to llm/prompts.yaml)

    Returns:
        PromptManager instance
    """
    if prompts_path is None:
        prompts_path = os.path.join(os.path.dirname(__file__), 'prompts.yaml')

    return PromptManager(prompts_path)
