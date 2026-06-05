# MCP Sampling Walkthrough

This project is a small practice implementation for the MCP advanced
certification sampling concept. It uses an MCP server over STDIO and a Python
client that handles sampling by calling OpenAI with the OpenAI SDK.

## What You Are Practicing

Sampling means the MCP server can ask the MCP client to request text from a
language model. The server does not call the model directly. Instead:

1. The client starts the MCP server.
2. The client registers a `sampling_callback`.
3. The client calls the server tool named `summarize`.
4. The server calls `ctx.session.create_message(...)`.
5. The MCP client receives that sampling request.
6. The client callback calls OpenAI.
7. The client returns a `CreateMessageResult`.
8. The server receives the generated text and returns it as the tool result.

## Files

- `server.py`: Defines the MCP server and the `summarize` tool.
- `client.py`: Starts the server, connects a sampling callback, calls OpenAI,
  and invokes the server tool.
- `pyproject.toml`: Defines Python version and dependencies.
- `.gitignore`: Ignores Python build files, virtual environments, and `.env`.

## Setup

Install `uv` if needed, then install dependencies:

```bash
uv sync
```

Set your OpenAI API key in your shell before running the client:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

You can optionally choose a model:

```powershell
$env:OPENAI_MODEL="gpt-5.4-mini"
```

## Run

```bash
uv run client.py
```

Expected result: the client prints a text content object containing OpenAI's
summary of the sample text.

## Step-by-Step Concept Check

### 1. Initiating Sampling

Check `server.py`:

```python
result = await ctx.session.create_message(...)
```

This is the key sampling call. The server is asking the client to create a
model message.

### 2. Sampling Message Format

Check `server.py`:

```python
SamplingMessage(
    role="user",
    content=TextContent(type="text", text=prompt),
)
```

The server sends MCP-native message objects, not Anthropic SDK dictionaries.

### 3. Sampling Callback

Check `client.py`:

```python
async def sampling_callback(
    context: RequestContext, params: CreateMessageRequestParams
):
```

This function receives the server's sampling request.

### 4. Message Conversion

Check `client.py`:

```python
messages.append({"role": "user", "content": content})
```

This converts MCP `SamplingMessage` objects into the format expected by the
OpenAI Responses API.

### 5. Calling OpenAI

Check `client.py`:

```python
response = await openai_client.responses.create(...)
```

This is where the MCP client sends the sampling request to OpenAI.

### 6. Returning Generated Text

Check `client.py`:

```python
return CreateMessageResult(...)
```

The callback wraps OpenAI's text response back into an MCP-compatible result.

### 7. Connecting the Callback

Check `client.py`:

```python
ClientSession(read, write, sampling_callback=sampling_callback)
```

Without this callback, the server's `create_message(...)` request cannot be
handled.

### 8. Getting the Final Tool Result

Check `client.py`:

```python
result = await session.call_tool(...)
print(result.content)
```

The client calls the MCP tool, the server performs sampling, and the final
generated text is returned as the tool output.

## Test Checklist

Run these checks while studying:

```bash
uv sync
uv run client.py
```

Then experiment:

1. Change `text_to_summarize` in `client.py` and run again.
2. Change `system_prompt` in `server.py` and observe the response style.
3. Temporarily remove `sampling_callback=sampling_callback` and confirm the
   sampling request cannot complete.
4. Add `print(params.messages)` inside `sampling_callback` to see the MCP
   message format.
5. Add `print(messages)` before `openai_client.responses.create(...)` to see
   the OpenAI API message format.
