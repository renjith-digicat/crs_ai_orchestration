"""Handles definition, creation of agent metadata."""

from enum import Enum
import os
from pydantic import BaseModel
from agents import AsyncOpenAI
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
)

from dotenv import load_dotenv

import system_prompts
from typing import Any, Sequence, Optional


load_dotenv(override=True)

ollama_base_url = os.getenv("OLLAMA_BASE_URL")
ollama_api_key = os.getenv("OLLAMA_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
groq_base_url = os.getenv("GROQ_BASE_URL")


OLLAMA_MODEL = "qwen3:4b"
GROQ_MODEL = "moonshotai/kimi-k2-instruct"
# GROQ_MODEL = "openai/gpt-oss-20b"

# Set the agents provider to be used
# AGENT_PROVIDER = "ollama"
AGENT_PROVIDER = "groq"
# AGENT_PROVIDER = "custom"  # mix of available providers

"""
Check supported models here - https://console.groq.com/docs/structured-outputs#supported-models
Should support `tool use` and `json schema mode`
"""


class AgentsMetaData(BaseModel):
    """
    Agent metadata schema to store agent information.
    """

    name: str
    instructions: str
    model: str
    client: AsyncOpenAI

    model_config = {"arbitrary_types_allowed": True}


# Utility classes and variable to switch LLM providers
class ProviderKey(str, Enum):
    OLLAMA = "ollama"
    GROQ = "groq"


CLIENTS = {
    ProviderKey.OLLAMA: AsyncOpenAI(api_key=ollama_api_key, base_url=ollama_base_url),
    ProviderKey.GROQ: AsyncOpenAI(api_key=groq_api_key, base_url=groq_base_url),
}

MODELS = {
    ProviderKey.OLLAMA: OLLAMA_MODEL,
    ProviderKey.GROQ: GROQ_MODEL,
}


def build_agent_metadata(
    base_name: str, instructions: str, provider: ProviderKey
) -> AgentsMetaData:
    return AgentsMetaData(
        name=f"{base_name} {provider.value.capitalize()}",
        instructions=instructions,
        model=MODELS[provider],
        client=CLIENTS[provider],
    )


# ##################################################################
# Build metadata for different agents with different providers

query_router_agent_metadata_ollama = build_agent_metadata(
    "Query Router Agent", system_prompts.query_router_instructions, ProviderKey.OLLAMA
)

query_router_agent_metadata_groq = build_agent_metadata(
    "Query Router Agent", system_prompts.query_router_instructions, ProviderKey.GROQ
)

keyword_generator_agent_metadata_ollama = build_agent_metadata(
    "Keyword Generator Agent",
    system_prompts.keyword_gen_instrctions,
    ProviderKey.OLLAMA,
)

keyword_generator_agent_metadata_groq = build_agent_metadata(
    "Keyword Generator Agent",
    system_prompts.keyword_gen_instrctions,
    ProviderKey.GROQ,
)

brave_web_search_agent_metadata_ollama = build_agent_metadata(
    "Brave Web Search Agent",
    system_prompts.brave_search_instructions,
    ProviderKey.OLLAMA,
)

brave_web_search_agent_metadata_groq = build_agent_metadata(
    "Brave Web Search Agent", system_prompts.brave_search_instructions, ProviderKey.GROQ
)

web_search_summariser_agent_metadata_ollama = build_agent_metadata(
    "Web Search Summariser Agent",
    system_prompts.summarise_search_result_instructions,
    ProviderKey.OLLAMA,
)

web_search_summariser_agent_metadata_groq = build_agent_metadata(
    "Web Search Summariser Agent",
    system_prompts.summarise_search_result_instructions,
    ProviderKey.GROQ,
)
# ##################################################################

if AGENT_PROVIDER == "ollama":
    router_agent_metadata = query_router_agent_metadata_ollama
    keyword_agent_metadata = keyword_generator_agent_metadata_ollama
    brave_search_agent_metadata = brave_web_search_agent_metadata_ollama
    web_search_summariser_agent_metadata = web_search_summariser_agent_metadata_ollama
elif AGENT_PROVIDER == "groq":
    router_agent_metadata = query_router_agent_metadata_groq
    keyword_agent_metadata = keyword_generator_agent_metadata_groq
    brave_search_agent_metadata = brave_web_search_agent_metadata_groq
    web_search_summariser_agent_metadata = web_search_summariser_agent_metadata_groq
elif AGENT_PROVIDER == "custom":
    router_agent_metadata = query_router_agent_metadata_ollama
    keyword_agent_metadata = keyword_generator_agent_metadata_ollama
    brave_search_agent_metadata = brave_web_search_agent_metadata_groq
    web_search_summariser_agent_metadata = web_search_summariser_agent_metadata_groq
else:
    print(f"Invalid AGENT_PROVIDER value: {AGENT_PROVIDER}")
    exit(1)


def build_agent(
    metadata: AgentsMetaData,
    output_type: Optional[Any] = None,
    mcp_servers: Optional[Sequence[Any]] = None,
    **extra_kwargs,
) -> Agent:
    """Build an agent from metadata."""
    # create kwargs based on metadata
    kwargs = dict(
        name=metadata.name,
        instructions=metadata.instructions,
        model=OpenAIChatCompletionsModel(
            model=metadata.model,
            openai_client=metadata.client,
        ),
    )

    # add optional output type and mcp servers to kwargs
    if output_type is not None:
        kwargs["output_type"] = output_type
    if mcp_servers is not None:
        kwargs["mcp_servers"] = list(mcp_servers)

    kwargs.update(extra_kwargs)

    return Agent(**kwargs)
