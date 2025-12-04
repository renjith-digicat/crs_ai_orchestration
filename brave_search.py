"""Utility functions for brave web search."""

import os
from dotenv import load_dotenv

from typing import Mapping
from urllib.parse import urlsplit, urlunsplit, urlencode, parse_qsl

load_dotenv(override=True)

brave_env = {"BRAVE_API_KEY": os.getenv("BRAVE_SEARCH_API_KEY")}

mcp_params = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": brave_env,
}


def get_web_search_query(search_query: str) -> str:
    """
    Build a strict prompt instructing the agent to perform a public web search
    (not internal memory) using the given search phrase.

    Parameters
    ----------
    search_query : str
        The search phrase to query on the web.

    Returns
    -------
    str
        A formatted prompt ready to be sent to the agent.
    """
    return f"""TASK: Use the public web (not memory) to search for:
            {search_query}

            REQUIREMENTS:
            - Return relevant results only.
            - Each result must include: title, snippet, and canonical URL.
            - Provide up to 5 high-quality results, ordered by usefulness.
            - Do not answer the query yourself, only return search results.
            """


def _md_escape(text: str) -> str:
    # minimal markdown escaper for titles
    return (
        text.replace("\\", "\\\\")
        .replace("*", r"\*")
        .replace("_", r"\_")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("(", r"\(")
        .replace(")", r"\)")
        .replace("#", r"\#")
        .replace("`", r"\`")
    )


def _normalize_url(u: str) -> str:
    # strip common tracking params, keep order stable
    sp = urlsplit(u.strip())
    q = [
        (k, v)
        for k, v in parse_qsl(sp.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
    ]
    return urlunsplit((sp.scheme, sp.netloc.lower(), sp.path, urlencode(q), ""))


def results_to_markdown(
    results: Mapping,
    max_refs_per_item: int = 10,
) -> str:
    """
    results: iterable of dict-like objects:
      { "summary": str, "references": [{"title": str, "url": str}, ...] }
    """
    lines = [""]
    summary = str(results.get("summary", "")).strip()
    refs = results.get("references") or []

    # de-duplicate references by normalized URL, preserve order
    seen = set()
    clean_refs = []
    for r in refs:
        url = _normalize_url(str(r.get("url", "")).strip())
        if not url or url in seen:
            continue
        seen.add(url)
        title = _md_escape(str(r.get("title", "") or url))
        clean_refs.append({"title": title, "url": url})
        if len(clean_refs) >= max_refs_per_item:
            break

    lines += [
        "",
        summary if summary else "_No summary provided._",
        "",
        "**References:**",
    ]
    if clean_refs:
        for i, r in enumerate(clean_refs[:5], start=1):
            # markdown link [title](url)
            lines.append(f"{i}. [{r['title']}]({r['url']})")
    else:
        lines.append("_No references available._")
    lines.append("")
    return "\n".join(lines)
