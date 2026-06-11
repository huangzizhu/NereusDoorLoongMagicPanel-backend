"""Web search and fetch tools using Tavily API.

Provides:
- webSearch: search the web via Tavily Search API
- webFetch: extract clean text content from a URL via Tavily Extract API

API key is read from TAVILY_API_KEY environment variable (optionally .env file),
with fallback to pyproject.toml [tool.ndlmpanel-agent].tavily_api_key.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any


def _projectRoot() -> Path:
    """Locate the project root (where pyproject.toml lives)."""
    return Path(__file__).resolve().parents[3]


def _loadEnvPyproject() -> dict[str, Any]:
    """Load pyproject.toml and return the [tool.ndlmpanel-agent] section, or empty dict."""
    pyproject = _projectRoot() / "pyproject.toml"
    if not pyproject.exists():
        return {}
    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return {}
    tool_section = data.get("tool", {}).get("ndlmpanel-agent", {})
    if not isinstance(tool_section, dict):
        return {}
    return tool_section


def _loadTavilyApiKey() -> str:
    """Read tavily_api_key from TAVILY_API_KEY env var, or pyproject.toml fallback."""
    # 1. Environment variable (highest priority)
    key = os.environ.get("TAVILY_API_KEY")
    if key:
        return key

    # 2. pyproject.toml fallback
    config = _loadEnvPyproject()
    key = config.get("tavily_api_key")
    if key and key != "tvly-YOUR_API_KEY_HERE":
        return key

    raise RuntimeError(
        "Tavily API key not configured. "
        "Set TAVILY_API_KEY in .env or export it as an environment variable, "
        "or set tavily_api_key in pyproject.toml under [tool.ndlmpanel-agent]."
    )


def webSearch(query: str, maxResults: int = 5) -> dict[str, Any]:
    """Search the web using Tavily and return structured results.

    Args:
        query: The search query string.
        maxResults: Maximum number of search results to return (1-20, default 5).

    Returns:
        A dict with keys:
          - success: bool
          - query: the original query
          - results: list of {title, url, content, score}
          - answer: optional AI-generated answer (if Tavily returns one)
          - error: error message on failure (only when success=false)
    """
    from tavily import TavilyClient

    try:
        api_key = _loadTavilyApiKey()
    except RuntimeError as exc:
        return {"success": False, "query": query, "results": [], "error": str(exc)}

    maxResults = max(1, min(20, maxResults))

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=maxResults,
            include_answer=True,
        )
    except Exception as exc:
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": f"Tavily search failed: {exc}",
        }

    results = []
    for item in response.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
            "score": item.get("score", 0),
        })

    answer = response.get("answer")
    return {
        "success": True,
        "query": query,
        "results": results,
        "answer": answer,
    }


def webFetch(url: str) -> dict[str, Any]:
    """Fetch and extract clean text content from a URL using Tavily.

    Args:
        url: The URL to fetch content from.

    Returns:
        A dict with keys:
          - success: bool
          - url: the original URL
          - content: extracted clean text content
          - error: error message on failure (only when success=false)
    """
    from tavily import TavilyClient

    try:
        api_key = _loadTavilyApiKey()
    except RuntimeError as exc:
        return {"success": False, "url": url, "content": "", "error": str(exc)}

    try:
        client = TavilyClient(api_key=api_key)
        response = client.extract(urls=[url])
    except Exception as exc:
        return {
            "success": False,
            "url": url,
            "content": "",
            "error": f"Tavily extract failed: {exc}",
        }

    results = response.get("results", [])
    if results:
        raw_content = results[0].get("raw_content", "")
        return {
            "success": True,
            "url": url,
            "content": raw_content,
        }

    failed = response.get("failed_results", [])
    if failed:
        error_msg = failed[0].get("error", "Unknown error")
        return {
            "success": False,
            "url": url,
            "content": "",
            "error": f"Failed to extract URL: {error_msg}",
        }

    return {
        "success": False,
        "url": url,
        "content": "",
        "error": "No content extracted from URL",
    }
