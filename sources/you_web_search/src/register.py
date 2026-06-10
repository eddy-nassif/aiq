# SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import enum
import logging
import os

import httpx
from pydantic import Field
from pydantic import SecretStr

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

# Track if we've already warned about missing API key to avoid duplicate warnings
_missing_key_warned = False


class LivecrawlMode(enum.Enum):
    web = "web"
    news = "news"
    all = "all"


class LivecrawlFormats(enum.Enum):
    html = "html"
    markdown = "markdown"


class SafesearchMode(enum.Enum):
    off = "off"
    moderate = "moderate"
    strict = "strict"


class YouWebSearchToolConfig(FunctionBaseConfig, name="you_web_search"):
    """
    Tool that retrieves relevant contexts from web search (using You.com) for the given question.
    Requires a YDC_API_KEY environment variable or api_key config.
    """

    api_key: SecretStr | None = Field(default=None, description="The API key for the You.com service")
    max_results: int = Field(
        default=5, ge=1, le=100, description="Maximum number of search results to return per section (web/news)"
    )
    max_retries: int = Field(default=3, description="Maximum number of retries for the search request")
    offset: int = Field(default=0, ge=0, le=9, description="Pagination offset in multiples of max_results")
    freshness: str | None = Field(
        default=None, description="Freshness filter: 'day', 'week', 'month', 'year', or 'YYYY-MM-DDtoYYYY-MM-DD'"
    )
    country: str | None = Field(default=None, description="Country code to focus results (e.g. 'US', 'GB')")
    language: str | None = Field(default=None, description="BCP 47 language code for results (e.g. 'EN', 'FR')")
    safesearch: SafesearchMode = Field(
        default=SafesearchMode.moderate, description="Safesearch filter: 'off', 'moderate', or 'strict'"
    )
    livecrawl: LivecrawlMode | None = Field(default=None, description="Livecrawl mode: 'web', 'news', or 'all'")
    livecrawl_formats: list[LivecrawlFormats] | None = Field(
        default=None, description="Livecrawl content formats: 'html', 'markdown', or both"
    )
    crawl_timeout: int = Field(default=10, ge=1, le=60, description="Max seconds to wait for livecrawl page content")
    include_domains: list[str] | None = Field(
        default=None, description="Restrict results to these domains (cannot combine with exclude_domains)"
    )
    exclude_domains: list[str] | None = Field(
        default=None, description="Exclude results from these domains (cannot combine with include_domains)"
    )
    boost_domains: list[str] | None = Field(
        default=None, description="Boost ranking for these domains (cannot combine with include_domains)"
    )
    max_content_length: int | None = Field(
        default=None,
        description="Max characters per result content. If set, truncates each result to reduce token usage.",
    )
    include_news_results: bool | None = Field(
        default=False,
        description="Whether or not to include news results. Include if you require up to date news results.",
    )


@register_function(config_type=YouWebSearchToolConfig)
async def you_web_search(tool_config: YouWebSearchToolConfig, builder: Builder):
    if not os.environ.get("YDC_API_KEY") and tool_config.api_key:
        os.environ["YDC_API_KEY"] = tool_config.api_key.get_secret_value()

    # Check if API key is available
    if not os.environ.get("YDC_API_KEY"):
        # Log warning only once to avoid duplicate warnings when multiple tools use You.com
        global _missing_key_warned
        if not _missing_key_warned:
            logger.warning(
                "YDC_API_KEY not found. The web search tool will be registered but will "
                "return an error when called. To enable: set YDC_API_KEY in your environment, "
                ".env file, or specify api_key in your workflow config."
            )
            _missing_key_warned = True

        # Yield a stub function that returns an error message
        async def _you_web_search_stub(question: str) -> str:
            """Web search tool (unavailable - missing YDC_API_KEY)."""
            return (
                "Error: Web search is unavailable because YDC_API_KEY is not set.\n"
                "To enable this tool:\n"
                "1. Get an API key from https://you.com/docs/quickstart\n"
                "2. Set the API key in your environment or in your .env file\n"
                "3. Restart the application"
            )

        yield FunctionInfo.from_fn(
            _you_web_search_stub,
            description=_you_web_search_stub.__doc__,
        )
        return

    async def _you_web_search(question: str) -> str:
        """Retrieves relevant contexts from web search (using You.com) for the given question.

        Args:
            question (str): The question to be answered.

        Returns:
            str: The web search results containing relevant documents and their URLs.
        """

        async def _post_request(query: str) -> dict:
            api_key = tool_config.api_key.get_secret_value() if tool_config.api_key else os.environ.get("YDC_API_KEY")
            headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
            payload = {
                k: v
                for k, v in {
                    "query": query,
                    "count": tool_config.max_results,
                    "offset": tool_config.offset,
                    "safesearch": tool_config.safesearch.value,
                    "freshness": tool_config.freshness,
                    "country": tool_config.country,
                    "language": tool_config.language,
                    "livecrawl": tool_config.livecrawl.value if tool_config.livecrawl else None,
                    "livecrawl_formats": [f.value for f in tool_config.livecrawl_formats]
                    if tool_config.livecrawl_formats
                    else None,
                    "crawl_timeout": tool_config.crawl_timeout if tool_config.livecrawl else None,
                    "include_domains": tool_config.include_domains,
                    "exclude_domains": tool_config.exclude_domains,
                    "boost_domains": tool_config.boost_domains,
                }.items()
                if v is not None
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://ydc-index.io/v1/search",
                    json=payload,
                    headers=headers,
                    timeout=tool_config.crawl_timeout,
                )
                response.raise_for_status()
                return response.json()

        def _format_response(response: dict) -> list[str]:
            formatted_results = []
            if "results" in response:
                if "web" not in response["results"]:
                    return []

                if tool_config.include_news_results and "news" in response["results"]:
                    all_results = response["results"]["news"] + response["results"]["web"]
                else:
                    all_results = response["results"]["web"]

                for result in all_results:
                    title = result.get("title", "")
                    url = result.get("url", "")
                    contents = result.get("contents", None)
                    if contents:
                        contents = contents.get("markdown", "")
                        if tool_config.max_content_length:
                            contents = contents[: tool_config.max_content_length]
                        if contents == "":
                            print(f"Got contents object, but no markdown. Received: {contents}")
                            contents = None

                    if not contents:
                        snippets_text = " ".join(result.get("snippets") or [])
                        description = result.get("description", "")
                        body = "\n".join(filter(None, [description, snippets_text]))
                    else:
                        body = contents
                    formatted_results.append(
                        f'<Document href="{url}">\n<title>\n{title}\n</title>\n{body}\n</Document>'
                    )
            return formatted_results

        for attempt in range(tool_config.max_retries):
            try:
                search_docs = await _post_request(query=question)
                if not isinstance(search_docs, dict):
                    raise ValueError(f"Search returned an error: {search_docs}")

                formatted_search_docs = _format_response(search_docs)
                if not formatted_search_docs:
                    raise ValueError("Search returned no results.")

                web_search_results = "\n\n---\n\n".join(formatted_search_docs)
                return web_search_results

            except Exception as e:
                if attempt == tool_config.max_retries - 1:
                    # On final attempt, return a user-friendly error message
                    error_msg = str(e)
                    if isinstance(e, ValueError):
                        return error_msg
                    if "401" in error_msg or "Unauthorized" in error_msg:
                        return (
                            "Error: Web search failed due to invalid API key (401 Unauthorized).\n"
                            "Please check your TAVILY_API_KEY and ensure it is valid.\n"
                        )
                    elif "error" in error_msg.lower():
                        return f"Error: Web search failed - {error_msg}"
                    else:
                        return f"Error: Web search failed - {error_msg}"
                await asyncio.sleep(2**attempt)

    yield FunctionInfo.from_fn(
        _you_web_search,
        description=_you_web_search.__doc__,
    )
