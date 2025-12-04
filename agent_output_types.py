"""Output types defintion for agent outputs.

These are used for schema enforcement and validation of LLM input and outputs."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal


class KeywordsOutput(BaseModel):
    explanation: str = Field(
        ...,
        description="Explanation of why this search phrase is a good fit for the search.",
    )
    search_query: str = Field(
        ...,
        description="Identified web search phrase that can be used to do a web search to gather relevant information from the web.",
    )


Intent = Literal[
    "clarification",
    "detect_monitor",
    "investigate_enrich",
    "act_orchestrate",
    "analyze_model",
    "report_compliance",
    "knowledge_support",
    "general",
    "harmful",
]


class ClassificationOutput(BaseModel):
    """
    Router decision for a single user query.
    """

    intent: Intent = Field(
        ...,
        description=(
            "One of 'clarification', 'detect_monitor', 'investigate_enrich' 'act_orchestrate', 'analyze_model', 'report_compliance', 'knowledge_support', 'general', or 'harmful'. "
        ),
    )
    explanation: Optional[str] = Field(
        None,
        description=(
            "Explanation or response depending on intent:\n"
            "- If 'clarification': ask a single, crisp follow-up question..\n"
            "- If 'general': provide a safe, complete answer if known; else respond with 'Sorry I don't know the answer to that.'.\n"
            "- If 'harmful': exactly 'Sorry, I am not supposed to answer that.'\n"
            "- For all other intents set explanation = null."
        ),
    )


class WebReference(BaseModel):
    title: str = Field(..., description="Human-readable page or article title.")
    url: HttpUrl = Field(..., description="Canonical URL to the source.")


class WebSearchResult(BaseModel):
    # model_config = ConfigDict(extra="forbid")  # disallow extra keys
    summary: str = Field(
        ..., description="Executive summary in 5-8 sentences, neutral tone, fact-based."
    )
    references: list[WebReference] = Field(
        ...,
        description="Deduplicated, relevance-ordered references that informed the summary.",
    )
