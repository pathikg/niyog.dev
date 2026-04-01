# LM Studio Setup for Niyog

Using LM Studio instead of Anthropic/OpenAI API for local LLM inference.

## Quick Start

### 1. Start LM Studio

```bash
# Open LM Studio application
# Go to "Server" tab
# Click "Start Server"

# Should output:
# [INFO] [LM STUDIO SERVER] Success! HTTP server listening on port 1234
```

### 2. Configure .env

```bash
cd ~/Documents/niyog.dev/backend
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/niyog_db
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model
LM_STUDIO_API_KEY=
```

**Note:** `LM_STUDIO_MODEL` should match the model name shown in LM Studio's "Chat" tab (e.g., `liquid/lfm2.5-1.2b`)

### 3. Install Dependencies

```bash
cd ~/Documents/niyog.dev/backend
pip install -e .
```

### 4. Run Tests

```bash
bash scripts/run_all_tests.sh
```

## How It Works

LM Studio provides an **OpenAI-compatible API** at `http://localhost:1234`:

```
GET  /v1/models           # List loaded models
POST /v1/chat/completions # Chat completion (OpenAI format)
```

Niyog uses **LangChain's ChatOpenAI** client pointing to this endpoint:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",  # Empty for local models
    model="local-model",
    temperature=0.7,
)

# Works just like OpenAI's ChatGPT
response = await llm.ainvoke([...])
```

## Configuration

### Get Model Name

In LM Studio's "Chat" tab, you'll see the model name (e.g., `liquid/lfm2.5-1.2b`).

Update `.env`:
```
LM_STUDIO_MODEL=liquid/lfm2.5-1.2b
```

### Change Port

If LM Studio is on a different port:

```
LM_STUDIO_BASE_URL=http://localhost:YOUR-PORT/v1
```

## Supported Operations

The OpenAI-compatible endpoint supports:

- ✅ **Chat completions** (used by Niyog)
- ✅ **Streaming** (SSE format)
- ✅ **Multi-turn conversations** (message history)
- ✅ **Temperature/top_p parameters**

## Example: Direct API Call

Test the local LLM directly:

```bash
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "liquid/lfm2.5-1.2b",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7
  }'
```

## Advantages

✅ **No API keys needed** — completely local  
✅ **Free** — no API billing  
✅ **Fast** — reduced latency (network-local)  
✅ **Privacy** — all data stays on your machine  
✅ **Offline** — works without internet  

## Troubleshooting

### "Connection refused" on localhost:1234

LM Studio server is not running. Start it:
1. Open LM Studio application
2. Go to "Server" tab
3. Click "Start Server"
4. Wait for "HTTP server listening on port 1234"

### "Model not found" error

Check the model name in LM Studio matches your `.env`:

**LM Studio Chat tab shows:** `liquid/lfm2.5-1.2b`

**`.env` should have:** `LM_STUDIO_MODEL=liquid/lfm2.5-1.2b`

### "Invalid response from LM Studio"

The local model may have different response behavior. If tests fail:

1. Check LM Studio is responding:
```bash
curl http://localhost:1234/v1/models
```

2. Check model is running:
   - Go to LM Studio "Server" tab
   - See if model is marked as "Loaded"
   - Manually load it if needed

3. Try a test query:
```bash
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"liquid/lfm2.5-1.2b","messages":[{"role":"user","content":"hi"}]}'
```

## Performance Notes

Local LLM inference times vary by model and hardware:

- **Small models** (1-3B params): 1-2 seconds per response
- **Medium models** (7-13B params): 5-10 seconds
- **Large models** (30B+ params): 20+ seconds

Niyog's Phase 3 test takes ~20 seconds due to 3 LLM calls (propose, classify, update).

## Next Steps

Once tests pass with LM Studio:

→ Phase 4: FastAPI endpoints + SSE streaming  
→ Phase 5: Talent onboarding graph  
→ Phase 6: File uploads

See: `/claude/plans/refactored-jingling-bubble.md`
