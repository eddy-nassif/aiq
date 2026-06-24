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

from langchain_youdotcom import YouSearchTool
from pydantic import Field
from pydantic import SecretStr

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

_missing_key_warned = False


class SafesearchMode(enum.Enum):
    off = "off"
    moderate = "moderate"
    strict = "strict"


class LivecrawlMode(enum.Enum):
    off = "off"
    web = "web"
    news = "news"
    all = "all"


class LivecrawlFormat(enum.Enum):
    off = "off"
    markdown = "markdown"
    html = "html"


class FreshnessMode(enum.Enum):
    off = None
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class YouWebSearchToolConfig(FunctionBaseConfig, name="you_web_search"):
    """
    Tool that retrieves relevant search results from web search (using You.com) for the given question.
    Uses LangChain's YouSearchAPIWrapper. Requires a YDC_API_KEY environment variable or api_key config.
    """

    # TODO: Write a test for each config param
    api_key: SecretStr | None = Field(default=None, description="The API key for the You.com service")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of search results to return")
    max_retries: int = Field(default=3, description="Maximum number of retries for the search request")
    safesearch: SafesearchMode = Field(
        default=SafesearchMode.moderate, description="Safesearch filter: 'off', 'moderate', or 'strict'"
    )
    livecrawl_mode: LivecrawlMode = Field(
        default=LivecrawlMode.web,
        description="If you want to retrieve page contents and the format to retrieve in: "
        "'off', 'web', 'news', or 'all'",
    )
    livecrawl_format: LivecrawlFormat = Field(
        default=LivecrawlFormat.markdown,
        description="What format you want to retrieve content in: 'off', 'markdown', 'html'",
    )
    freshness: FreshnessMode = Field(
        default=FreshnessMode.off,
        description="Restrict your search to a certain freshness: 'off', 'day', 'week', 'month', 'year'",
    )
    max_content_length: int | None = Field(
        default=None,
        description="Max characters per result content. If set, truncates each result to reduce token usage.",
    )
    include_news_results: bool = Field(
        default=False,
        description="Whether or not you want to include news results. If False, filter out documents whose "
        "metadata 'source' is 'news'.",
    )
    timeout: float | None = Field(
        default=None,
        description="Timeout in seconds for each search request. None means no timeout.",
    )


@register_function(config_type=YouWebSearchToolConfig)
async def you_web_search(tool_config: YouWebSearchToolConfig, builder: Builder):
    if not os.environ.get("YDC_API_KEY") and tool_config.api_key:
        os.environ["YDC_API_KEY"] = tool_config.api_key.get_secret_value()

    if not os.environ.get("YDC_API_KEY"):
        global _missing_key_warned
        if not _missing_key_warned:
            logger.warning(
                "YDC_API_KEY not found. The web search tool will be registered but will "
                "return an error when called. To enable: set YDC_API_KEY in your environment, "
                ".env file, or specify api_key in your workflow config."
            )
            _missing_key_warned = True

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

    api_key = tool_config.api_key.get_secret_value() if tool_config.api_key else os.environ.get("YDC_API_KEY")

    wrapper_kwargs = {
        k: v
        for k, v in {
            "ydc_api_key": api_key,
            "count": tool_config.max_results,
            "livecrawl": tool_config.livecrawl_mode.value,
            "livecrawl_formats": tool_config.livecrawl_format.value,
            "freshness": tool_config.freshness.value,
            "safesearch": tool_config.safesearch.value,
        }.items()
        if v is not None
    }
    you_search_tool = YouSearchTool(api_wrapper=wrapper_kwargs)

    _query_cache: dict[str, str] = {}
    _CACHE_MAX_SIZE = 500

    async def _you_web_search(question: str) -> str:
        """Retrieves relevant contexts from web search (using You.com) for the given question.

        Args:
            question (str): The question to be answered.

        Returns:
            str: The web search results containing relevant documents and their URLs.
        """
        if question in _query_cache:
            logger.debug("Cache hit for query: %s", question[:80])
            return _query_cache[question]

        def _format_documents(search_docs) -> list[str]:
            # TODO: Need to format so that we don't get a content too large error from LLM
            #   But so many different LLMs can be used, how will we know what to truncate to?
            #   Can I read config and use max_tokens?
            formatted_results = []
            for doc in search_docs:
                if not tool_config.include_news_results and doc.metadata.get("source") == "news":
                    continue
                title = doc.metadata.get("title", "")
                url = doc.metadata.get("url", "")
                description = doc.metadata.get("description", "")
                content = getattr(doc, "page_content")
                if content:
                    if tool_config.max_content_length:
                        content = content[: tool_config.max_content_length]
                    result = (
                        f'<Document href="{url}">\n<title>\n{title}\n</title>\n{description}\n{content}\n</Document>'
                    )
                    formatted_results.append(result)
                else:
                    result = f'<Document href="{url}">\n<title>\n{title}\n</title>\n{description}\n</Document>'
                    formatted_results.append(result)

            return formatted_results

        for attempt in range(tool_config.max_retries):
            try:
                coro = you_search_tool.api_wrapper.results_async(question)
                docs = await (asyncio.wait_for(coro, timeout=tool_config.timeout) if tool_config.timeout else coro)
                if not docs:
                    raise ValueError("Search returned no results.")

                formatted = _format_documents(search_docs=docs)
                if not formatted:
                    raise ValueError("Search returned results but failed to format.")

                result = "\n\n---\n\n".join(formatted)
                if len(_query_cache) >= _CACHE_MAX_SIZE:
                    _query_cache.pop(next(iter(_query_cache)))
                _query_cache[question] = result
                return result

            except Exception as e:
                if attempt == tool_config.max_retries - 1:
                    error_msg = str(e)
                    if isinstance(e, ValueError):
                        return error_msg
                    if "401" in error_msg or "Unauthorized" in error_msg:
                        return (
                            "Error: Web search failed due to invalid API key (401 Unauthorized).\n"
                            "Please check your YDC_API_KEY and ensure it is valid.\n"
                        )
                    return f"Error: Web search failed after {tool_config.max_retries} attempts: {error_msg}"
                await asyncio.sleep(2**attempt)

    yield FunctionInfo.from_fn(
        _you_web_search,
        description=_you_web_search.__doc__,
    )
