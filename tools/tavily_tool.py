from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def tavily_search(query):
    if not client.api_key:
        return "Hotel search unavailable: missing TAVILY_API_KEY."

    try:
        response = client.search(
            query=query,
            max_results=5
        )
    except Exception as exc:
        return f"Hotel search failed: {exc}"

    if not isinstance(response, dict) or "results" not in response:
        return "Hotel search returned no results."

    results = []
    for i, r in enumerate(response.get("results", [])[:5], 1):
        title = r.get("title", "Unknown")
        url = r.get("uri", "")
        snippet = r.get("content", "").strip()

        if len(snippet) > 300:
            snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

        results.append(f"{i}. **{title}**\n{url}\n{snippet}")

    if not results:
        return "No hotel results available."

    return "\n\n".join(results)