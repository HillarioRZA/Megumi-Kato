"""
Orchestrator Module for Project Anima.

Acts as the central routing manager connecting prompt building, sliding-window short-term memory,
persistent SQLite memory injection, and LLM execution.
"""

import logging
from collections import deque
from typing import Any, Dict, List, Optional

from core.config import Config, get_config
from core.llm_client import OllamaClient
from core.tool_dispatcher import ToolDispatcher
from memory.manager import MemoryManager
from personality.personality_builder import PersonalityBuilder
from tools.registry import ALL_TOOL_SCHEMAS
from core.time_cache import TimeCache

logger = logging.getLogger("anima.orchestrator")

MAX_TOOL_ITERATIONS: int = 3


class Orchestrator:
    """
    Central router for processing user requests, managing sliding-window memory,
    coordinating LLM execution, and handling tool-calling loops.

    Supports dependency injection for OllamaClient, PersonalityBuilder, MemoryManager,
    and ToolDispatcher.
    """

    def __init__(
        self,
        llm_client: OllamaClient,
        personality_builder: Optional[PersonalityBuilder] = None,
        memory_manager: Optional[MemoryManager] = None,
        tool_dispatcher: Optional[ToolDispatcher] = None,
        time_cache: Optional[TimeCache] = None,
        config: Optional[Config] = None,
    ) -> None:
        """
        Initialize Orchestrator with LLM client, personality builder, memory manager, and tool dispatcher.

        Args:
            llm_client (OllamaClient): Injected Ollama client instance.
            personality_builder (Optional[PersonalityBuilder]): Injected personality builder instance.
            memory_manager (Optional[MemoryManager]): Injected persistent memory coordinator.
            tool_dispatcher (Optional[ToolDispatcher]): Injected tool dispatcher instance.
            config (Optional[Config]): System configuration instance. If None, uses global config.
        """
        self.llm_client = llm_client
        self.personality_builder = personality_builder
        self.memory_manager = memory_manager
        self.time_cache = time_cache
        self.tool_dispatcher = tool_dispatcher
        self.config = config or get_config()

        # Bounded sliding window history in RAM (default 16 messages = 8 turns)
        self.history: deque[Dict[str, str]] = deque(maxlen=self.config.short_term_memory_limit)

        # Recover prior chat history from persistent storage if memory_manager is present
        if self.memory_manager:
            recovered_messages = self.memory_manager.load_recent_chat(
                limit=self.config.short_term_memory_limit
            )
            for msg in recovered_messages:
                self.history.append(msg)
            if recovered_messages:
                logger.info(
                    f"Recovered {len(recovered_messages)} prior messages from persistent storage."
                )

        logger.info(
            f"Initialized Orchestrator [Sliding Window Limit: {self.config.short_term_memory_limit}, Tools Enabled: {self.tool_dispatcher is not None}]"
        )

    def process_message(
        self,
        user_input: str,
        personality_prompt: Optional[str] = None,
        memory_context: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Process user message through history routing, tool calling loop, and LLM execution.

        Args:
            user_input (str): Input text from user.
            personality_prompt (Optional[str]): Custom system prompt for assistant character.
            memory_context (Optional[List[Dict[str, str]]]): Custom memory context turns.
            tools (Optional[List[Any]]): Tool definitions for function calling.
            **kwargs (Any): Additional dynamic arguments passed to LLM client.

        Returns:
            str: Assistant response text.
        """
        if not user_input or not user_input.strip():
            logger.warning("Received empty user input.")
            return ""

        user_text = user_input.strip()
        logger.info(f"Processing message [Input length: {len(user_text)}]")

        # 1. Determine system personality prompt
        sys_prompt = personality_prompt
        if not sys_prompt and self.personality_builder:
            sys_prompt = self.personality_builder.get_system_prompt()

        if sys_prompt:
            logger.debug(f"Assembled system prompt:\n{sys_prompt}")

        messages: List[Dict[str, Any]] = []

        # 2. Append system personality prompt
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        # 3. Inject relevant long-term memories if available
        if self.memory_manager and not memory_context:
            mem_prompt = self.memory_manager.get_memory_context_prompt(query=user_text)
            if mem_prompt:
                messages.append({"role": "system", "content": mem_prompt})

        if self.time_cache:
            messages.append({
                "role": "system",
                "content": (f"[Time Context — approximate] Around {self.time_cache.get_cached()}."
                "You already know the current time from this context. "
                "Answer general time questions directly without calling any tools."
                ),
            })
        # 4. Prepend few-shot turns as real conversation turns
        if self.personality_builder:
            few_shot_messages = self.personality_builder.get_few_shot_messages()
            messages.extend(few_shot_messages)

        # 5. Inject custom memory context if explicitly passed
        if memory_context:
            for mem in memory_context:
                messages.append(mem)

        # 6. Include sliding window conversation history
        messages.extend(list(self.history))

        # 7. Append current user input
        messages.append({"role": "user", "content": user_text})

        # 8. Multi-turn Tool Calling Loop
        tool_schemas = tools if tools is not None else (ALL_TOOL_SCHEMAS if self.tool_dispatcher else None)
        final_content = ""

        for iteration in range(MAX_TOOL_ITERATIONS):
            chat_response = self.llm_client.chat(
                messages=messages,
                tools=tool_schemas,
                **kwargs,
            )

            tool_calls = getattr(chat_response, "tool_calls", None) or []
            content = getattr(chat_response, "content", "")

            if not tool_calls:
                final_content = content
                break

            logger.info(
                f"Model requested {len(tool_calls)} tool call(s) "
                f"[Iteration {iteration + 1}/{MAX_TOOL_ITERATIONS}]"
            )

            # Append the assistant's tool-call turn to messages
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })

            # Execute all requested tools and append results
            if self.tool_dispatcher:
                tool_result_messages = self.tool_dispatcher.dispatch_all(tool_calls)
                messages.extend(tool_result_messages)
            else:
                logger.warning("Tool calls requested but no ToolDispatcher available.")
                final_content = content
                break
        else:
            # Loop exhausted without a final answer — force-return last content
            logger.warning(
                f"Max tool iterations ({MAX_TOOL_ITERATIONS}) reached without a final answer."
            )
            final_content = content or "Maaf, ada yang aneh nih. Coba tanya lagi?"

        response_text = final_content

        # 9. Update in-memory sliding window deque
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": response_text})

        # 10. Auto-persist to SQLite persistent storage
        if self.memory_manager:
            self.memory_manager.save_chat_turn(role="user", content=user_text)
            self.memory_manager.save_chat_turn(role="assistant", content=response_text)

        logger.info(
            f"Message processed successfully. Short-term history size: {len(self.history)}."
        )

        return response_text

    def get_history(self) -> List[Dict[str, str]]:
        """
        Retrieve a copy of the current in-memory sliding window conversation history.

        Returns:
            List[Dict[str, str]]: List of role and content dictionaries.
        """
        return list(self.history)

    def clear_history(self, clear_persistent_db: bool = True) -> None:
        """
        Clear in-memory sliding window and optionally persistent database chat history.

        Args:
            clear_persistent_db (bool): If True, also clears SQLite chat_history table.
        """
        self.history.clear()
        if clear_persistent_db and self.memory_manager:
            self.memory_manager.clear_chat()
        logger.info("Cleared orchestrator conversation history.")
