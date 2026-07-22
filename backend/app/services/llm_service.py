"""LLM service layer using LiteLLM for unified model access."""

import logging
from typing import Optional
import asyncio

from litellm import completion, acompletion
from litellm.exceptions import APIError, APIConnectionError, RateLimitError, AuthenticationError

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for making LLM calls via LiteLLM."""

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        """
        Initialize LLM service.

        Args:
            base_url: Ollama base URL
        """
        self.base_url = base_url
        # Configure LiteLLM to use Ollama
        self.text_model = settings.TEXT_MODEL
        self.classifier_model = settings.CLASSIFIER_MODEL

        logger.info(f"LLM Service initialized with base_url={base_url}")
        logger.info(f"Text model: {self.text_model}")
        logger.info(f"Classifier model: {self.classifier_model}")

    async def generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate text using the specified model.

        Args:
            prompt: User prompt
            model: Model name (e.g., "ollama/llama3.2:8b")
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            system_prompt: Optional system prompt

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            logger.debug(f"Generating with model={model}, max_tokens={max_tokens}")

            # Call LiteLLM
            response = await acompletion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                api_base=self.base_url,
                timeout=300,  # 5 minute timeout
            )

            # Extract text
            generated_text = response.choices[0].message.content

            logger.info(f"Generation successful for model={model}")

            return generated_text

        except APIConnectionError as e:
            logger.error(f"Failed to connect to LLM service: {e}")
            raise LLMError(f"Connection failed: {str(e)}")

        except RateLimitError as e:
            logger.error(f"Rate limited: {e}")
            raise LLMError(f"Rate limited: {str(e)}")

        except AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            raise LLMError(f"Authentication failed: {str(e)}")

        except APIError as e:
            logger.error(f"LLM API error: {e}")
            raise LLMError(f"API error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}", exc_info=True)
            raise LLMError(f"Unexpected error: {str(e)}")

    def generate_sync(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate text synchronously (blocking).

        Args:
            prompt: User prompt
            model: Model name
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            logger.debug(f"Generating (sync) with model={model}")

            # Call LiteLLM synchronously
            response = completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                api_base=self.base_url,
                timeout=300,
            )

            generated_text = response.choices[0].message.content

            logger.info(f"Generation successful (sync) for model={model}")

            return generated_text

        except Exception as e:
            logger.error(f"Error during sync generation: {e}")
            raise LLMError(f"Generation failed: {str(e)}")


class LLMError(Exception):
    """Exception for LLM service errors."""

    pass


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def init_llm_service(base_url: str = settings.OLLAMA_BASE_URL) -> LLMService:
    """Initialize the LLM service."""
    global _llm_service
    _llm_service = LLMService(base_url=base_url)
    return _llm_service
