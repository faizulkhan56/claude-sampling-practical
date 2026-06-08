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

If `uv` is not installed on Windows PowerShell:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

After installing `uv`, restart your terminal and check:

```powershell
uv --version
```

### Git Bash Environment Variables

If you are using Git Bash on Windows, set environment variables with `export`:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-4o-mini"
```

Then run:

```bash
uv sync
uv run client.py
```

Keep your API key private. Do not commit it, paste it into code, or write it in
`README.md`.

### PowerShell Environment Variables

If you are using Windows PowerShell, use `$env:`:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

You can optionally choose a model:

```powershell
$env:OPENAI_MODEL="gpt-5.4-mini"
```

## Run

For a normal run with your OpenAI key:

Git Bash:

```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-4o-mini"
uv sync
uv run client.py
```

PowerShell:

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
$env:OPENAI_MODEL="gpt-4o-mini"
uv sync
uv run client.py
```

If you want to try another OpenAI model, change only `OPENAI_MODEL`:

```bash
export OPENAI_MODEL="gpt-5.4-mini"
uv run client.py
```

After the first setup, you usually only need:

```bash
uv run client.py
```

Expected result: the client prints a text content object containing OpenAI's
summary of the sample text.

With debug prints enabled, you should also see:

```text
MCP sampling request:
...
OpenAI messages:
...
```

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

The server sends MCP-native message objects, not OpenAI API dictionaries.

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

## Theory: How The Code Calls Each Other

The easiest way to understand this project is to follow the request path.

### 1. `client.py` starts `server.py`

In `client.py`:

```python
server_params = StdioServerParameters(
    command="uv",
    args=["run", "server.py"],
)
```

This means the client will start the MCP server by running:

```bash
uv run server.py
```

The client and server communicate through STDIO.

### 2. `client.py` connects the sampling callback

In `client.py`:

```python
async with ClientSession(
    read, write, sampling_callback=sampling_callback
) as session:
```

This is very important. It tells MCP:

When the server asks for sampling, call `sampling_callback`.

Without this callback, the server can ask for sampling, but the client will not
know how to call the LLM.

### 3. `client.py` calls the MCP tool

In `client.py`:

```python
result = await session.call_tool(
    name="summarize",
    arguments={"text_to_summarize": "..."},
)
```

This calls the `summarize` tool from `server.py`.

### 4. `server.py` receives the tool call

In `server.py`:

```python
@mcp.tool()
async def summarize(text_to_summarize: str, ctx: Context):
```

This function runs when the client calls:

```python
session.call_tool(name="summarize", ...)
```

The `ctx` object lets the server talk back to the MCP client.

### 5. `server.py` asks for sampling

In `server.py`:

```python
result = await ctx.session.create_message(
    messages=[
        SamplingMessage(
            role="user",
            content=TextContent(type="text", text=prompt),
        )
    ],
    max_tokens=4000,
    system_prompt="You are a helpful research assistant.",
)
```

This is the main sampling line.

The server is saying:

```text
Client, please ask an LLM to answer this prompt.
```

The server does not use `OPENAI_API_KEY`. The client owns the API key.

### 6. `client.py` receives the sampling request

In `client.py`:

```python
async def sampling_callback(
    context: RequestContext, params: CreateMessageRequestParams
):
```

This function receives the sampling request from `server.py`.

The debug prints show what arrived from the server:

```python
print("MCP sampling request:")
print(params.messages)
```

When you run the project, this helps you see the MCP-native message format.

### 7. `client.py` converts MCP messages to OpenAI messages

In `client.py`:

```python
messages.append({"role": "user", "content": content})
```

MCP sends `SamplingMessage` objects. OpenAI expects message dictionaries. This
conversion step changes the message format.

The debug prints show the converted OpenAI format:

```python
print("OpenAI messages:")
print(messages)
```

### 8. `client.py` calls OpenAI

In `client.py`:

```python
response = await openai_client.responses.create(
    model=model,
    input=messages,
    instructions=system_prompt,
    max_output_tokens=max_tokens,
)
```

This is where your `OPENAI_API_KEY` is used. The key is read automatically by
the OpenAI SDK from the environment variable:

```bash
OPENAI_API_KEY
```

### 9. `client.py` returns the result to `server.py`

In `client.py`:

```python
return CreateMessageResult(
    role="assistant",
    model=model,
    content=TextContent(type="text", text=text),
)
```

The client wraps the OpenAI output in an MCP-compatible result.

### 10. `server.py` returns the final tool output

In `server.py`:

```python
if result.content.type == "text":
    return result.content.text
```

The server receives the text from the client and returns it as the final result
of the `summarize` tool.

Full flow:

```text
client.py starts server.py
client.py calls summarize tool
server.py runs summarize
server.py calls ctx.session.create_message
client.py sampling_callback receives request
client.py calls OpenAI
client.py returns CreateMessageResult
server.py returns final text
client.py prints result.content
```

## Debug Practice

The project already includes these debug prints in `client.py`.

Inside `sampling_callback`:

```python
print("MCP sampling request:")
print(params.messages)
```

This shows what `server.py` sends to `client.py`.

Inside `chat`, before the OpenAI API call:

```python
print("OpenAI messages:")
print(messages)
```

This shows how MCP messages are converted into OpenAI message format.

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
4. Check the `MCP sampling request:` debug output to see the MCP message
   format.
5. Check the `OpenAI messages:` debug output to see the OpenAI API message
   format.

## Full Flow In One Picture

```text
Git Bash
export OPENAI_API_KEY
export OPENAI_MODEL
uv run client.py
        ↓
client.py starts
        ↓
asyncio.run(run())
        ↓
stdio_client(server_params)
        ↓
starts: uv run server.py
        ↓
server.py starts MCP server with stdio
        ↓
ClientSession(read, write, sampling_callback=...)
        ↓
session.initialize()
        ↓
client calls server tool: summarize
        ↓
server.py summarize() runs
        ↓
server.py creates prompt
        ↓
server.py calls ctx.session.create_message(...)
        ↓
MCP sends sampling request to client
        ↓
client.py sampling_callback(context, params) runs
        ↓
params.messages contains server prompt
        ↓
chat(params.messages, max_tokens, system_prompt)
        ↓
chat converts MCP messages to OpenAI messages
        ↓
openai_client.responses.create(...)
        ↓
OpenAI returns answer
        ↓
client returns CreateMessageResult to server
        ↓
server returns result.content.text
        ↓
client receives tool result
        ↓
print(result.content)
```

The heart of the concept is this:

```text
Client calls server tool.
Server tool asks client to call LLM.
Client calls OpenAI.
Client returns LLM answer to server.
Server returns final tool result to client.
```
