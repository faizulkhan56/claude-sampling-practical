from mcp.server.fastmcp import Context, FastMCP
from mcp.types import SamplingMessage, TextContent

mcp = FastMCP(name="Demo Server")


@mcp.tool()
async def summarize(text_to_summarize: str, ctx: Context):
    prompt = f"""
        Please summarize the following text in 3 bullet points:
        {text_to_summarize}
    """

    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user", content=TextContent(type="text", text=prompt)
            )
        ],
        max_tokens=4000,
        system_prompt="You are a strict technical teacher. Explain simply.",
    )

    if result.content.type == "text":
        return result.content.text
    raise ValueError("Sampling failed")


if __name__ == "__main__":
    mcp.run(transport="stdio")
