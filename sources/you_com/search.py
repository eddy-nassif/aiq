# TODO: THIS IS JUST FOR LOCAL TESTING, DO NOT MERGE
#!/usr/bin/env python3
import asyncio
import os
import sys
from unittest.mock import MagicMock

from you_com.register import SafesearchMode
from you_com.register import YouWebSearchToolConfig
from you_com.register import you_web_search

# --- Configure here ---
QUERY = "latest AI news"
MAX_RESULTS = 5
MAX_CONTENT_LENGTH = None  # int or None
SAFESEARCH = SafesearchMode.moderate
INCLUDE_NEWS = False
# ----------------------


# def _load_dotenv():
#     for path in (
#         os.path.join(os.path.dirname(__file__), ".env"),
#         os.path.join(os.path.dirname(__file__), "../../.env"),
#     ):
#         if os.path.exists(path):
#             with open(path) as f:
#                 for line in f:
#                     line = line.strip()
#                     if line and not line.startswith("#") and "=" in line:
#                         k, _, v = line.partition("=")
#                         os.environ.setdefault(k.strip(), v.strip())
#             break


async def main() -> None:
    if not os.environ.get("YDC_API_KEY"):
        print("Error: YDC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    config = YouWebSearchToolConfig(
        max_results=MAX_RESULTS,
        max_content_length=MAX_CONTENT_LENGTH,
        safesearch=SAFESEARCH,
        include_news_results=INCLUDE_NEWS,
    )

    print(f"\nSearching: {QUERY!r}\n{'=' * 60}")

    async with you_web_search(config, MagicMock()) as info:
        result = await info.single_fn(QUERY)

    print(result)


if __name__ == "__main__":
    # _load_dotenv()
    asyncio.run(main())
