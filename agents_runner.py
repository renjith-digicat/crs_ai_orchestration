"""Main agent runner - handles the logic for agent invocation and data flow."""

import os
import io
from contextlib import redirect_stdout

from agents import (
    Runner,
    set_tracing_disabled,
    set_tracing_export_api_key,
    trace,
)
from dotenv import load_dotenv

from agents.mcp import MCPServerStdio

import agent_metadata
import agent_output_types
import brave_search

from agents.model_settings import ModelSettings
from agents.mcp.util import create_static_tool_filter


load_dotenv(override=True)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Must set this if want to use trace
openai_api_key = os.getenv("OPENAI_API_KEY")


# Defining some agents beforehand
router_agent = agent_metadata.build_agent(
    metadata=agent_metadata.router_agent_metadata,
    output_type=agent_output_types.ClassificationOutput,
)

keyword_agent = agent_metadata.build_agent(
    metadata=agent_metadata.keyword_agent_metadata,
    output_type=agent_output_types.KeywordsOutput,
)

search_summariser_agent = agent_metadata.build_agent(
    metadata=agent_metadata.web_search_summariser_agent_metadata,
    output_type=agent_output_types.WebSearchResult,
)


def format_history_for_context(
    history: list[dict[str, str]], max_turns: int = 6
) -> str:
    """
    Convert Streamlit-style history [{"role":"user"/"assistant","content":...}, ...]
    into a compact text context. Trim to last `max_turns` pairs to avoid token bloat.
    """
    # keep only user/assistant messages
    cleaned = [m for m in history if m.get("role") in ("user", "assistant")]
    # take the last N*2 messages
    trimmed = cleaned[-2 * max_turns :]
    lines = []
    for m in trimmed:
        prefix = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{prefix}: {m['content']}")
    return "\n".join(lines)


# Openai tracing
DISABLE_TRACING = False
set_tracing_disabled(DISABLE_TRACING)
# this key will only be used to upload traces
set_tracing_export_api_key(openai_api_key)


async def process_query(query: str, history: list[dict[str, str]] | None = None):
    # Build a combined input that includes prior conversation context
    history_context = format_history_for_context(history or [], max_turns=6)
    if history_context.strip():
        router_input = (
            "You are given prior conversation context. Use it only to stay consistent.\n\n"
            "=== Conversation (most recent last) ===\n"
            f"{history_context}\n"
            "=== End conversation ===\n\n"
            f"Final user message: {query}"
        )
    else:
        router_input = query

    results_summaries: list[str] = []

    # Prepare a buffer to capture prints
    buffer = io.StringIO()
    # Redirect stdout to the buffer for capturing prints
    with redirect_stdout(buffer):
        # Agent pipeline logic
        with trace("CRS Orchestrator Agent"):
            router_result = await Runner.run(router_agent, input=router_input)
            print(f"\nintent: {router_result.final_output.intent}")
            print(f"explanation: {router_result.final_output.explanation}")
            if router_result.final_output.intent == "knowledge_support":
                keyword_result = await Runner.run(keyword_agent, input=query)
                search_query = keyword_result.final_output.search_query
                print("\nagent identified search phrase:\n", search_query)

                # Use Brave search agent to get summaries with web search
                async with MCPServerStdio(
                    params=brave_search.mcp_params,
                    client_session_timeout_seconds=30,
                    tool_filter=create_static_tool_filter(
                        allowed_tool_names=["brave_web_search"]  # show ONLY this tool
                    ),
                    cache_tools_list=True,
                ) as mcp_server:
                    brave_search_agent = agent_metadata.build_agent(
                        metadata=agent_metadata.brave_search_agent_metadata,
                        # output_type=agent_output_types.WebSearchResult,
                        mcp_servers=[mcp_server],
                        model_settings=ModelSettings(
                            # tool_choice="required",  #"brave_web_search",  # force MCP tool to use - or use "required" - not working with groq
                            parallel_tool_calls=False,  # optional: keep MCP call to one
                            temperature=0.1,  # 0 -> eterministic output is forced
                            max_tokens=512,
                        ),
                        tool_use_behavior="stop_on_first_tool",
                    )
                    raw_search_result = await Runner.run(
                        brave_search_agent,
                        brave_search.get_web_search_query(search_query),
                    )

                    search_summary = await Runner.run(
                        search_summariser_agent,
                        input=raw_search_result.final_output,
                    )

                    def model_to_dict(x):
                        return x.model_dump() if hasattr(x, "model_dump") else dict(x)

                    results_summaries = [
                        brave_search.results_to_markdown(
                            model_to_dict(search_summary.final_output)
                        )
                    ]
                    # Should not remove this print line below as this is the identifier for thinkilng log end
                    print("-THINKING ENDS-")
            elif router_result.final_output.intent == "general":
                # handling general queries for now and later will not be answered by the agent
                results_summaries = [
                    "[Note: General queries not related will not be answered from next version...] \n"
                    + router_result.final_output.explanation
                ]
            else:
                # For other intents, the explanation is the result
                if router_result.final_output.explanation is None:
                    results_summaries = [
                        "[Workflows yet to be implemented. Please try other queries...]"
                    ]
                else:
                    results_summaries = [router_result.final_output.explanation]
            # --- End of agent pipeline logic ---
    # Everythin within the `redirect_stdout` block, all printed text is in buffer
    full_logs = buffer.getvalue()
    # Separate reasoning and result (if needed):
    # For example, everything up to "Search Summary:" is reasoning, and after that is final result.
    return full_logs, results_summaries
