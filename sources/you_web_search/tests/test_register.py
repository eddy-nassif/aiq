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

"""Tests for the you_web_search NAT registration."""

import os
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr
from you_web_search.register import YouWebSearchToolConfig
from you_web_search.register import you_web_search


def _make_web_result(title="Title", url="https://example.com", snippets=None, description="", contents_markdown=None):
    result = {"title": title, "url": url, "snippets": snippets or [], "description": description}
    if contents_markdown is not None:
        result["contents"] = {"markdown": contents_markdown}
    return result


def _make_api_response(web_results=None, news_results=None):
    response = {"results": {"web": web_results or []}}
    if news_results is not None:
        response["results"]["news"] = news_results
    return response


@pytest.fixture(autouse=True)
def _reset_warn_flag():
    import you_web_search.register as reg

    reg._missing_key_warned = False
    yield
    reg._missing_key_warned = False


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("YDC_API_KEY", raising=False)


@pytest.fixture
def mock_httpx(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_client)
    cm.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr("you_web_search.register.httpx.AsyncClient", MagicMock(return_value=cm))
    return mock_client, mock_response


class TestYouWebSearchToolConfig:
    def test_defaults(self):
        config = YouWebSearchToolConfig()
        assert config.max_results == 5
        assert config.api_key is None
        assert config.max_retries == 3
        assert config.offset == 0
        assert config.safesearch.value == "moderate"
        assert config.livecrawl is None
        assert config.max_content_length is None
        assert config.include_news_results is False

    def test_all_fields(self):
        from you_web_search.register import LivecrawlFormats
        from you_web_search.register import LivecrawlMode
        from you_web_search.register import SafesearchMode

        config = YouWebSearchToolConfig(
            max_results=10,
            api_key=SecretStr("test-key"),
            max_retries=1,
            offset=2,
            freshness="week",
            country="US",
            language="EN",
            safesearch=SafesearchMode.strict,
            livecrawl=LivecrawlMode.web,
            livecrawl_formats=[LivecrawlFormats.markdown],
            crawl_timeout=30,
            include_domains=["example.com"],
            max_content_length=500,
            include_news_results=True,
        )
        assert config.max_results == 10
        assert config.api_key.get_secret_value() == "test-key"
        assert config.offset == 2
        assert config.freshness == "week"
        assert config.country == "US"
        assert config.safesearch.value == "strict"
        assert config.livecrawl.value == "web"
        assert config.max_content_length == 500
        assert config.include_news_results is True

    def test_inherits_from_function_base_config(self):
        from nat.data_models.function import FunctionBaseConfig

        assert issubclass(YouWebSearchToolConfig, FunctionBaseConfig)


class TestYouWebSearchStub:
    async def test_stub_when_no_api_key(self):
        config = YouWebSearchToolConfig()
        builder = MagicMock()

        async with you_web_search(config, builder) as info:
            result = await info.single_fn("anything")

        assert "YDC_API_KEY" in result
        assert "unavailable" in result.lower()


class TestYouWebSearchLive:
    async def test_api_key_from_config_sets_env(self, mock_httpx, monkeypatch):
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            [_make_web_result("Title", "https://a.example", snippets=["snippet"])]
        )

        config = YouWebSearchToolConfig(api_key=SecretStr("key-from-config"))
        builder = MagicMock()

        async with you_web_search(config, builder) as info:
            out = await info.single_fn("question")

        assert os.environ.get("YDC_API_KEY") == "key-from-config"
        assert "https://a.example" in out

    async def test_successful_search_formats_documents(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            [
                _make_web_result("Title A", "https://a.example", snippets=["Body A"]),
                _make_web_result("Title B", "https://b.example", snippets=["Body B"]),
            ]
        )

        config = YouWebSearchToolConfig(max_results=2)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("query")

        assert "Title A" in out
        assert "Title B" in out
        assert "Body A" in out
        assert "Body B" in out
        assert "---" in out

    async def test_contents_markdown_used_over_snippets(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            [
                _make_web_result(
                    "T", "https://a.example", snippets=["fallback snippet"], contents_markdown="full markdown body"
                ),
            ]
        )

        config = YouWebSearchToolConfig()
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "full markdown body" in out
        assert "fallback snippet" not in out

    async def test_fallback_combines_snippets_and_description(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            [
                _make_web_result("T", "https://a.example", snippets=["snippet text"], description="desc text"),
            ]
        )

        config = YouWebSearchToolConfig()
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "snippet text" in out
        assert "desc text" in out

    async def test_truncates_content(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            [
                _make_web_result("T", "https://a.example", contents_markdown="abcdefghijklmnop"),
            ]
        )

        config = YouWebSearchToolConfig(max_content_length=5)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "abcde" in out
        assert "abcdefgh" not in out

    async def test_include_news_results_merges_news_and_web(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            web_results=[_make_web_result("Web Result", "https://web.example", snippets=["web body"])],
            news_results=[_make_web_result("News Result", "https://news.example", snippets=["news body"])],
        )

        config = YouWebSearchToolConfig(include_news_results=True)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "https://web.example" in out
        assert "https://news.example" in out

    async def test_no_web_key_in_response_returns_error(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = {"results": {"news": []}}

        config = YouWebSearchToolConfig(max_retries=1)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "no results" in out.lower()

    async def test_empty_results_returns_error(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response([])

        config = YouWebSearchToolConfig(max_retries=1)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "no results" in out.lower()

    async def test_non_dict_response_returns_error(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        monkeypatch.setattr("you_web_search.register.asyncio.sleep", _no_sleep)
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = "upstream error string"

        config = YouWebSearchToolConfig(max_retries=1)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "error" in out.lower()

    async def test_retries_then_succeeds(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        monkeypatch.setattr("you_web_search.register.asyncio.sleep", _no_sleep)
        mock_client, mock_response = mock_httpx

        good_response = MagicMock()
        good_response.raise_for_status = MagicMock()
        good_response.json.return_value = _make_api_response(
            [_make_web_result("T", "https://a.example", snippets=["ok"])]
        )
        mock_client.post.side_effect = [RuntimeError("transient"), good_response]

        config = YouWebSearchToolConfig(max_retries=3)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "ok" in out
        assert mock_client.post.call_count == 2

    async def test_401_returns_friendly_message(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        monkeypatch.setattr("you_web_search.register.asyncio.sleep", _no_sleep)
        mock_client, mock_response = mock_httpx
        mock_client.post.side_effect = RuntimeError("401 Unauthorized")

        config = YouWebSearchToolConfig(max_retries=2)
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            out = await info.single_fn("q")

        assert "401" in out

    async def test_payload_excludes_none_values(self, mock_httpx, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            [_make_web_result("T", "https://a.example", snippets=["body"])]
        )

        config = YouWebSearchToolConfig()
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            await info.single_fn("q")

        payload = mock_client.post.call_args.kwargs["json"]
        assert "freshness" not in payload
        assert "livecrawl" not in payload
        assert "include_domains" not in payload

    async def test_livecrawl_params_sent_in_payload(self, mock_httpx, monkeypatch):
        from you_web_search.register import LivecrawlFormats
        from you_web_search.register import LivecrawlMode

        monkeypatch.setenv("YDC_API_KEY", "test-key")
        mock_client, mock_response = mock_httpx
        mock_response.json.return_value = _make_api_response(
            [_make_web_result("T", "https://a.example", snippets=["body"])]
        )

        config = YouWebSearchToolConfig(livecrawl=LivecrawlMode.web, livecrawl_formats=[LivecrawlFormats.markdown])
        builder = MagicMock()
        async with you_web_search(config, builder) as info:
            await info.single_fn("q")

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["livecrawl"] == "web"
        assert payload["livecrawl_formats"] == ["markdown"]
        assert "crawl_timeout" in payload


async def _no_sleep(_):
    return None
