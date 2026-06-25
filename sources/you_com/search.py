# TODO: THIS IS JUST FOR LOCAL TESTING, DO NOT MERGE
#!/usr/bin/env python3
import asyncio
import os
import sys
from unittest.mock import MagicMock

from you_com.register import LivecrawlMode
from you_com.register import SafesearchMode
from you_com.register import YouWebSearchToolConfig
from you_com.register import you_web_search

# --- Configure here ---
QUERY = "Who won the 2025 Seattle Mayoral election?"
MAX_RESULTS = 5
LIVECRAWL_MODE = LivecrawlMode.web
MAX_CONTENT_LENGTH = 10  # int or None
SAFESEARCH = SafesearchMode.moderate
INCLUDE_NEWS = False
# ----------------------


async def main() -> None:
    if not os.environ.get("YDC_API_KEY"):
        print("Error: YDC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    config = YouWebSearchToolConfig(
        max_results=MAX_RESULTS,
        max_content_length=MAX_CONTENT_LENGTH,
        safesearch=SAFESEARCH,
        include_news_results=INCLUDE_NEWS,
        livecrawl_mode=LIVECRAWL_MODE,
    )

    print(f"\nSearching: {QUERY!r}\n{'=' * 60}")

    async with you_web_search(config, MagicMock()) as info:
        result = await info.single_fn(QUERY)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
