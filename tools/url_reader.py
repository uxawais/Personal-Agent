import httpx
from bs4 import BeautifulSoup
from tools.registry import register_tool


@register_tool(
    name="read_url",
    description="Read and extract the main text content from a URL/webpage.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to read"},
        },
        "required": ["url"],
    },
)
async def read_url(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        response = await client.get(url, headers={"User-Agent": "Chorus Agent/1.0"})
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    content = "\n".join(lines)

    if len(content) > 10000:
        content = content[:10000] + "\n... (truncated)"

    return content
