# TODO: THIS IS JUST FOR LOCAL TESTING, DO NOT MERGE
#!/usr/bin/env python3
import asyncio
import os
import sys
from unittest.mock import MagicMock

from you_com.register import ResearchEffort
from you_com.register import YouFinanceResearchToolConfig
from you_com.register import you_finance_research

# --- Configure here ---
QUERY = "What drove NVIDIA's revenue growth in FY2025?"
RESEARCH_EFFORT = ResearchEffort.deep
# ----------------------


async def main() -> None:
    if not os.environ.get("YDC_API_KEY"):
        print("Error: YDC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    config = YouFinanceResearchToolConfig(
        research_effort=RESEARCH_EFFORT,
    )

    print(f"\nResearching: {QUERY!r}\n{'=' * 60}")

    async with you_finance_research(config, MagicMock()) as info:
        result = await info.single_fn(QUERY)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
