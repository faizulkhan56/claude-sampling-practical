import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.session import RequestContext
from mcp.client.stdio import stdio_client
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    SamplingMessage,
    TextContent,
)
from openai import AsyncOpenAI

openai_client = AsyncOpenAI()
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

server_params = StdioServerParameters(
    command="uv",
    args=["run", "server.py"],
)


async def chat(
    input_messages: list[SamplingMessage],
    max_tokens=4000,
    system_prompt: str | None = None,
):
    messages = []
    for msg in input_messages:
        if msg.role == "user" and msg.content.type == "text":
            content = (
                msg.content.text
                if hasattr(msg.content, "text")
                else str(msg.content)
            )
            messages.append({"role": "user", "content": content})
        elif msg.role == "assistant" and msg.content.type == "text":
            content = (
                msg.content.text
                if hasattr(msg.content, "text")
                else str(msg.content)
            )
            messages.append({"role": "assistant", "content": content})

    print("OpenAI messages:")
    print(messages)

    response = await openai_client.responses.create(
        model=model,
        input=messages,
        instructions=system_prompt,
        max_output_tokens=max_tokens,
    )

    return response.output_text


async def sampling_callback(
    context: RequestContext, params: CreateMessageRequestParams
):
    print("MCP sampling request:")
    print(params.messages)

    # Call OpenAI using the OpenAI SDK.
    system_prompt = (
        getattr(params, "system_prompt", None)
        or getattr(params, "systemPrompt", None)
    )
    max_tokens = (
        getattr(params, "max_tokens", None)
        or getattr(params, "maxTokens", None)
        or 4000
    )
    text = await chat(params.messages, max_tokens, system_prompt)

    return CreateMessageResult(
        role="assistant",
        model=model,
        content=TextContent(type="text", text=text),
    )


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write, sampling_callback=sampling_callback
        ) as session:
            await session.initialize()

            result = await session.call_tool(
                name="summarize",
                arguments={
                    "text_to_summarize": (
                        "MCP sampling is a capability in the Model Context "
                        "Protocol that allows an MCP server to request "
                        "language-model completion through the connected "
                        "client instead of calling the model directly. This is "
                        "important because the server does not need to own or "
                        "manage model credentials, API keys, billing access, "
                        "or provider-specific configuration. Instead, the "
                        "client acts as the trusted control point and decides "
                        "whether the sampling request should be approved, "
                        "which model should be used, and how the final "
                        "response should be returned. This design keeps the "
                        "user or host application in control of model access "
                        "while still allowing servers to build intelligent "
                        "features such as summarization, rewriting, "
                        "classification, planning, or context-aware "
                        "assistance. In practical terms, MCP sampling makes it "
                        "possible for a tool server to ask for AI help without "
                        "becoming an AI provider itself. It also improves "
                        "security because sensitive credentials remain with "
                        "the client, and every sampling request can be "
                        "reviewed, approved, blocked, or modified based on "
                        "the client's policy."
                    )
                },
            )
            print(result.content)


if __name__ == "__main__":
    asyncio.run(run())
