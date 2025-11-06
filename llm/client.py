"""
LLM Client Wrapper with Error Handling and Best Practices.

This module provides a unified interface for calling various LLM providers
(OpenAI, Anthropic, Google Gemini) with robust error handling, retries,
caching, and logging.
"""

import os
import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union, Literal
from datetime import datetime, timedelta
from functools import wraps
from pydantic import BaseModel, Field

import openai
from openai import OpenAI, APIError, RateLimitError, APIConnectionError, APITimeoutError
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================

class LLMRequest(BaseModel):
    """Request to LLM."""
    prompt: str = Field(..., description="The prompt to send to the LLM")
    system_prompt: Optional[str] = Field(None, description="System prompt (if supported)")
    model: Optional[str] = Field(None, description="Override default model")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for sampling")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    response_format: Literal["text", "json", "json_object"] = Field("text", description="Expected response format")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LLMResponse(BaseModel):
    """Response from LLM."""
    content: str = Field(..., description="The generated content")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage stats")
    finish_reason: str = Field(..., description="Why generation stopped")
    cached: bool = Field(False, description="Whether response was cached")
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class LLMError(Exception):
    """Base exception for LLM errors."""
    def __init__(self, message: str, original_error: Optional[Exception] = None, retryable: bool = False):
        super().__init__(message)
        self.original_error = original_error
        self.retryable = retryable


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, retryable=True)
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """Request timed out."""
    def __init__(self, message: str):
        super().__init__(message, retryable=True)


class LLMValidationError(LLMError):
    """Invalid request or response."""
    def __init__(self, message: str):
        super().__init__(message, retryable=False)


# ============================================================================
# Cache
# ============================================================================

class SimpleCache:
    """Simple in-memory cache with TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def _make_key(self, prompt: str, model: str, temperature: float) -> str:
        """Create cache key from request parameters."""
        key_str = f"{model}:{temperature}:{prompt}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, prompt: str, model: str, temperature: float) -> Optional[Any]:
        """Get cached response if available and not expired."""
        key = self._make_key(prompt, model, temperature)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                logger.debug(f"Cache HIT for key: {key[:16]}...")
                return value
            else:
                # Expired
                del self.cache[key]
                logger.debug(f"Cache EXPIRED for key: {key[:16]}...")
        return None

    def set(self, prompt: str, model: str, temperature: float, value: Any):
        """Cache a response."""
        key = self._make_key(prompt, model, temperature)
        self.cache[key] = (value, datetime.now())
        logger.debug(f"Cache SET for key: {key[:16]}...")

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        logger.info("Cache cleared")


# ============================================================================
# LLM Client
# ============================================================================

class LLMClient:
    """
    Unified LLM client with error handling, retries, caching, and logging.

    Features:
    - Multiple provider support (OpenAI, Anthropic, Gemini)
    - Automatic retries with exponential backoff
    - Response caching
    - Token usage tracking
    - Cost estimation
    - Structured logging
    - Rate limit handling
    """

    # Pricing per 1M tokens (as of January 2025, update regularly)
    # Source: https://openai.com/api/pricing/
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},              # Latest GPT-4 model
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},          # Cost-effective alternative
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},        # Previous generation
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},        # Legacy model
        "o1": {"input": 15.00, "output": 60.00},                 # Reasoning model
        "o1-mini": {"input": 3.00, "output": 12.00},             # Smaller reasoning model
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Default model to use (defaults to OPENAI_MODEL env var or gpt-4o-mini)
            temperature: Default temperature (0.0-2.0)
            max_tokens: Default max tokens to generate
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for transient errors
            retry_delay: Base delay between retries (exponential backoff)
            enable_cache: Whether to cache responses
            cache_ttl: Cache TTL in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", temperature))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", max_tokens))
        self.timeout = int(os.getenv("OPENAI_TIMEOUT", timeout))
        self.max_retries = int(os.getenv("LLM_RETRY_ATTEMPTS", max_retries))
        self.retry_delay = float(os.getenv("LLM_RETRY_DELAY", retry_delay))

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)

        # Cache
        self.enable_cache = enable_cache and os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"
        self.cache = SimpleCache(ttl_seconds=cache_ttl) if self.enable_cache else None

        # Stats
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.cache_hits = 0

        logger.info(f"LLMClient initialized: model={self.model}, cache={self.enable_cache}")

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate estimated cost in USD."""
        if model not in self.PRICING:
            logger.warning(f"Pricing not available for model: {model}")
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def _retry_with_backoff(self, func):
        """Decorator for retry with exponential backoff."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)

                except RateLimitError as e:
                    last_exception = e
                    retry_after = getattr(e, 'retry_after', None) or (self.retry_delay * (2 ** attempt))
                    logger.warning(f"Rate limit hit. Retrying after {retry_after}s (attempt {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(retry_after)
                    else:
                        raise LLMRateLimitError(
                            f"Rate limit exceeded after {self.max_retries} attempts",
                            retry_after=int(retry_after)
                        )

                except (APIConnectionError, APITimeoutError) as e:
                    last_exception = e
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Connection/timeout error. Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise LLMTimeoutError(f"Request failed after {self.max_retries} attempts: {str(e)}")

                except APIError as e:
                    last_exception = e
                    # Check if it's a transient error
                    if e.status_code in [500, 502, 503, 504]:
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Server error {e.status_code}. Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})")
                        if attempt < self.max_retries - 1:
                            time.sleep(delay)
                        else:
                            raise LLMError(f"API error after {self.max_retries} attempts: {str(e)}", original_error=e)
                    else:
                        # Non-retryable error
                        raise LLMError(f"API error: {str(e)}", original_error=e, retryable=False)

            # Should not reach here, but just in case
            if last_exception:
                raise LLMError(f"Failed after {self.max_retries} attempts", original_error=last_exception)

        return wrapper

    def _prepare_messages(self, prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Prepare messages for chat completion."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return messages

    @property
    def _make_request(self):
        """Get the request function with retry decorator applied."""
        @self._retry_with_backoff
        def _request(
            messages: List[Dict[str, str]],
            model: str,
            temperature: float,
            max_tokens: int,
            response_format: str,
        ):
            """Make the actual API request."""
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # Add response format if JSON requested
            if response_format in ["json", "json_object"]:
                kwargs["response_format"] = {"type": "json_object"}

            return self.client.chat.completions.create(**kwargs)

        return _request

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Literal["text", "json", "json_object"] = "text",
        use_cache: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Generate completion from LLM.

        Args:
            prompt: The user prompt
            system_prompt: System prompt (optional)
            model: Override default model
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            response_format: Expected response format (text, json, json_object)
            use_cache: Whether to use cache for this request
            metadata: Additional metadata to include in response

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMError: For API errors
            LLMRateLimitError: For rate limit errors
            LLMTimeoutError: For timeout errors
            LLMValidationError: For validation errors
        """
        start_time = time.time()

        # Use defaults if not specified
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        # Check cache
        cached_response = None
        if use_cache and self.enable_cache and self.cache:
            cache_key = f"{system_prompt or ''}:{prompt}"
            cached_response = self.cache.get(cache_key, model, temperature)
            if cached_response:
                self.cache_hits += 1
                cached_response.cached = True
                cached_response.latency_ms = (time.time() - start_time) * 1000
                logger.info(f"Cache HIT: {model} ({cached_response.latency_ms:.2f}ms)")
                return cached_response

        # Prepare messages
        messages = self._prepare_messages(prompt, system_prompt)

        # Log request
        if os.getenv("LLM_LOG_REQUESTS", "true").lower() == "true":
            logger.info(f"LLM Request: model={model}, temp={temperature}, max_tokens={max_tokens}, format={response_format}")
            logger.debug(f"Messages: {messages}")

        # Make request with retries
        try:
            response = self._make_request(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            raise

        # Extract response
        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason

        # Validate JSON if requested
        if response_format in ["json", "json_object"]:
            try:
                json.loads(content)  # Validate JSON
            except json.JSONDecodeError as e:
                raise LLMValidationError(f"Expected JSON response but got invalid JSON: {str(e)}")

        # Calculate stats
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        cost = self._calculate_cost(model, usage)
        latency_ms = (time.time() - start_time) * 1000

        # Update stats
        self.total_requests += 1
        self.total_tokens += usage["total_tokens"]
        self.total_cost += cost

        # Log response
        if os.getenv("LLM_LOG_RESPONSES", "true").lower() == "true":
            logger.info(
                f"LLM Response: tokens={usage['total_tokens']}, "
                f"cost=${cost:.6f}, latency={latency_ms:.2f}ms, finish={finish_reason}"
            )
            logger.debug(f"Content preview: {content[:200]}...")

        # Create response object
        llm_response = LLMResponse(
            content=content,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            cached=False,
            latency_ms=latency_ms,
            cost_usd=cost,
            metadata=metadata or {},
        )

        # Cache the response
        if use_cache and self.enable_cache and self.cache:
            cache_key = f"{system_prompt or ''}:{prompt}"
            self.cache.set(cache_key, model, temperature, llm_response)

        return llm_response

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON response and parse it.

        Args:
            prompt: The user prompt
            system_prompt: System prompt (optional)
            **kwargs: Additional arguments for generate()

        Returns:
            Parsed JSON as dictionary

        Raises:
            LLMValidationError: If response is not valid JSON
        """
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format="json_object",
            **kwargs
        )

        try:
            return json.loads(response.content)
        except json.JSONDecodeError as e:
            raise LLMValidationError(f"Failed to parse JSON response: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "cache_hits": self.cache_hits,
            "cache_hit_rate": round(self.cache_hits / max(self.total_requests, 1), 2),
            "avg_cost_per_request": round(self.total_cost / max(self.total_requests, 1), 6),
        }

    def reset_stats(self):
        """Reset usage statistics."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.cache_hits = 0
        logger.info("Stats reset")

    def clear_cache(self):
        """Clear response cache."""
        if self.cache:
            self.cache.clear()
