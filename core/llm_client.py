"""
Ollama LLM Client Module for Project Anima.

Handles HTTP communication with the local Ollama API server, including model inference,
custom error handling, and logging.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional
import httpx

from core.config import Config, get_config

logger = logging.getLogger("anima.llm_client")


@dataclass
class ChatResponse:
    """
    Structured response from an Ollama chat completion.

    Attributes:
        content (str): The text content of the response (may be empty if
            the model only returned tool calls).
        tool_calls (List[Dict[str, Any]]): Raw tool_calls list from Ollama
            response, empty list if the model did not request any tools.
    """
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


class OllamaClientError(Exception):
    """Base exception class for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaClientError):
    """Raised when connection to the Ollama server fails."""
    pass


class OllamaAPIError(OllamaClientError):
    """Raised when Ollama API returns an error response."""
    pass


class OllamaClient:
    """
    Dedicated client for Ollama LLM HTTP API interaction.

    Attributes:
        config (Config): System configuration instance.
        base_url (str): Formatted Ollama API base URL.
        model_name (str): Configured model identifier.
        client (httpx.Client): HTTP client instance.
    """

    def __init__(self, config: Optional[Config] = None, timeout: Optional[float] = None) -> None:
        """
        Initialize the OllamaClient instance.

        Args:
            config (Optional[Config]): Configuration instance. If None, uses global config.
            timeout (Optional[float]): Request timeout in seconds. Defaults to config setting if None.
        """
        self.config = config or get_config()
        self.base_url = self.config.ollama_base_url.rstrip("/")
        self.model_name = self.config.model_name
        self.timeout = timeout if timeout is not None else self.config.ollama_timeout
        self.client = httpx.Client(timeout=self.timeout)

        logger.info(
            f"Initialized OllamaClient [Base URL: {self.base_url}, Model: {self.model_name}, Timeout: {self.timeout}s]"
        )

    def check_connection(self) -> bool:
        """
        Check if the Ollama API server is online and accessible.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        url = f"{self.base_url}/api/tags"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                logger.debug("Ollama connection health check passed.")
                return True
            else:
                logger.warning(
                    f"Ollama health check returned status code {response.status_code}"
                )
                return False
        except httpx.RequestError as exc:
            logger.error(f"Failed to connect to Ollama server at {url}: {exc}")
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Send a single completion request to Ollama /api/generate.

        Args:
            prompt (str): Prompt string for the model.
            system_prompt (Optional[str]): Optional system prompt.
            **kwargs (Any): Additional options (temperature, num_ctx, etc.).

        Returns:
            str: Generated text content.

        Raises:
            OllamaConnectionError: If network connection to Ollama fails.
            OllamaAPIError: If Ollama API returns an error response.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        chat_response = self.chat(messages=messages, **kwargs)
        return chat_response.content

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """
        Send a multi-turn chat request to Ollama /api/chat.

        Args:
            messages (List[Dict[str, Any]]): Conversation history array with role and content keys.
            tools (Optional[List[Dict[str, Any]]]): Optional list of tool schemas for function calling.
            **kwargs (Any): Additional model options to override defaults.

        Returns:
            ChatResponse: Structured response with text content and parsed tool_calls.

        Raises:
            OllamaConnectionError: If network connection to Ollama fails.
            OllamaAPIError: If Ollama API returns an error status or error payload.
        """
        url = f"{self.base_url}/api/chat"

        # Prepare model options
        options: Dict[str, Any] = {
            "num_ctx": kwargs.pop("num_ctx", self.config.num_ctx),
            "temperature": kwargs.pop("temperature", self.config.temperature),
            "num_predict": kwargs.pop("num_predict", self.config.num_predict_default),
        }
        options.update(kwargs)

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": options,
            "think": self.config.thinking_mode_default,
        }
        if tools:
            payload["tools"] = tools

        logger.info(
            f"Sending chat request to Ollama [Model: {self.model_name}, Num Predict: {options['num_predict']}, Messages: {len(messages)}, Tools: {len(tools) if tools else 0}]"
        )

        try:
            response = self.client.post(url, json=payload)
        except httpx.ConnectError as exc:
            msg = f"Cannot connect to Ollama server at {self.base_url}. Ensure Ollama service is running."
            logger.error(msg)
            raise OllamaConnectionError(msg) from exc
        except httpx.TimeoutException as exc:
            msg = f"Request to Ollama timed out after {self.timeout} seconds."
            logger.error(msg)
            raise OllamaConnectionError(msg) from exc
        except httpx.RequestError as exc:
            msg = f"HTTP request failed: {exc}"
            logger.error(msg)
            raise OllamaConnectionError(msg) from exc

        if response.status_code != 200:
            error_text = response.text
            msg = f"Ollama API returned HTTP {response.status_code}: {error_text}"
            logger.error(msg)
            raise OllamaAPIError(msg)

        try:
            data = response.json()
        except Exception as exc:
            msg = f"Failed to parse JSON response from Ollama: {response.text}"
            logger.error(msg)
            raise OllamaAPIError(msg) from exc

        if "error" in data:
            msg = f"Ollama API Error: {data['error']}"
            logger.error(msg)
            raise OllamaAPIError(msg)

        message_obj = data.get("message", {})
        content = message_obj.get("content", "") or ""

        tool_calls: List[Dict[str, Any]] = []
        try:
            raw_tool_calls = message_obj.get("tool_calls", [])
            if isinstance(raw_tool_calls, list):
                tool_calls = raw_tool_calls
        except Exception as exc:
            logger.warning(
                f"Unexpected error extracting tool_calls from Ollama response: {exc}"
            )
            tool_calls = []

        eval_count = data.get("eval_count", "N/A")
        logger.info(
            f"Successfully received chat response from Ollama. [Generated Tokens: {eval_count}, Tool Calls: {len(tool_calls)}]"
        )

        return ChatResponse(content=content, tool_calls=tool_calls)

    def close(self) -> None:
        """Close the underlying HTTP client session."""
        self.client.close()
        logger.debug("Closed OllamaClient HTTP session.")

    def __enter__(self) -> "OllamaClient":
        """Support context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """Support context manager exit by automatically closing HTTP session."""
        self.close()
