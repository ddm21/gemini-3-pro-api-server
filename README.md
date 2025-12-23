# Gemini 3.0 API Server

A FastAPI server that exposes Google's Gemini 3.0 models (Pro and Flash) as a REST API with support for flexible prompts (text/file URLs), image URLs, JSON schemas, and per-request configurable model selection, thinking levels, and media resolution.

## Features

- ✅ **Security First** - API key authentication, rate limiting, SSRF protection
- ✅ Multiple model support - Choose between Gemini 3 Pro or Flash
- ✅ Flexible prompts - Pass as text or load from URLs
- ✅ Multiple image support - Image URLs
- ✅ Structured JSON output - Use schemas for guaranteed structure
- ✅ Configurable thinking levels - Model-specific levels (per request)
- ✅ Configurable media resolution - LOW, MEDIUM, or HIGH (per request)
- ✅ Dynamic system prompts - Control AI behavior per request

## Quick Start

### Local Setup

#### Create a virtual environment and Install dependencies from requirements.txt
**On Linux/macOS**
```
source gemini-pro-3/bin/activate && gemini-pro-3\Scripts\activate.bat
```

**On Windows**
```
python3 -m venv gemini-pro-3 && gemini-pro-3\Scripts\activate.bat
```

**Install requirements**
```
pip install -r requirements.txt
```

**Deactivate the environment (when finished)**
```
deactivate
```

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Create `.env` file:**

```env
# Required: Your Gemini API key
GEMINI_API_KEY=your-gemini-api-key-here

# Required: API key for authenticating requests to your server
SERVER_API_KEY=your-strong-random-server-api-key-here

# Required: Comma-separated allowed CORS origins
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Optional: Rate limit (default: 10/minute)
RATE_LIMIT=10/minute
```

> **⚠️ Security Warning**: Never commit your `.env` file to version control!

3. **Run the server:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

### Docker Setup

1. **Build the image:**

```bash
docker build -t gemini-api .
```

2. **Run the container:**

```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-gemini-api-key-here \
  -e SERVER_API_KEY=your-server-api-key-here \
  -e ALLOWED_ORIGINS=http://localhost:3000 \
  gemini-api
```

## 🔒 Security

### Authentication

**All API endpoints (except `/health`) require authentication** via the `X-API-Key` header.

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-server-api-key-here" \
  -d '{"user_prompt": "Hello, world!"}'
```

### Security Features

- ✅ **API Key Authentication** - Secure all endpoints
- ✅ **Rate Limiting** - Prevent abuse (configurable, default: 10 req/min)
- ✅ **SSRF Protection** - Blocks private IPs, localhost, cloud metadata
- ✅ **Input Validation** - Strict Pydantic models with validators
- ✅ **Security Headers** - X-Frame-Options, CSP, HSTS, etc.
- ✅ **CORS Control** - Environment-based origin whitelisting
- ✅ **Error Sanitization** - No internal details exposed to clients
- ✅ **Docker Security** - Runs as non-root user

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | - | Your Google Gemini API key |
| `SERVER_API_KEY` | ✅ Yes | - | API key for authenticating requests to your server |
| `ALLOWED_ORIGINS` | ✅ Yes | - | Comma-separated list of allowed CORS origins |
| `RATE_LIMIT` | ❌ No | `10/minute` | Rate limit (e.g., "10/minute", "100/hour") |
| `REQUEST_TIMEOUT` | ❌ No | `15` | Timeout for external requests (seconds) |
| `DEFAULT_TEMPERATURE` | ❌ No | `0.6` | Default temperature for generation |
| `DEFAULT_TOP_P` | ❌ No | `0.4` | Default top_p for generation |
| `DEFAULT_MAX_OUTPUT_TOKENS` | ❌ No | `12000` | Default max output tokens |

**See [SECURITY.md](SECURITY.md) for detailed security guidelines.**



## API Usage

### Endpoint: `POST /generate`

**Content-Type:** `application/json`

### Request Body Schema

```json
{
  "user_prompt": "string (required)",
  "user_prompt_type": "text" | "file" (optional, default: "text"),
  "system_prompt": "string" (optional),
  "system_prompt_type": "text" | "file" (optional, default: "text"),
  "image_urls": ["url1", "url2"] (optional),
  "json_schema": { ... } (optional),
  "model": "gemini-3-pro-preview" | "gemini-3-flash-preview" (optional, default: "gemini-3-pro-preview"),
  "thinking_level": "LOW" | "HIGH" (Pro) or "minimal" | "low" | "medium" | "high" (Flash) (optional, default: "HIGH"),
  "media_resolution": "LOW" | "MEDIUM" | "HIGH" (optional, default: "MEDIUM")
}
```

### Response Format

```json
{
  "output": "...",
  "input_tokens": 1234,
  "output_tokens": 567,
  "total_tokens": 1801
}
```

**Note:** `output` is a string by default, or a JSON object/array when `json_schema` is provided.

## CURL Examples

### 1. Simple Text Generation

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-server-api-key-here" \
  -d '{
    "user_prompt": "Write a haiku about coding"
  }'
```

### 2. With System Prompt

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-server-api-key-here" \
  -d '{
    "user_prompt": "Explain quantum computing",
    "system_prompt": "You are a physics professor teaching undergraduates. Use simple analogies."
  }'
```

### 3. Load Prompts from URLs

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "https://yourserver.com/prompts/landing-page-task.txt",
    "user_prompt_type": "file",
    "system_prompt": "https://yourserver.com/prompts/system.txt",
    "system_prompt_type": "file"
  }'
```

### 4. URL-Based Images

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Analyze this landing page",
    "image_urls": [
      "https://example.com/screenshot1.png",
      "https://example.com/screenshot2.png"
    ]
  }'
```

### 5. Using Gemini 3 Flash

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Write a short story about AI",
    "model": "gemini-3-flash-preview",
    "thinking_level": "medium"
  }'
```

### 6. With Thinking Level and Media Resolution

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Analyze this product image in detail",
    "image_urls": ["https://example.com/product.jpg"],
    "model": "gemini-3-pro-preview",
    "thinking_level": "HIGH",
    "media_resolution": "HIGH"
  }'
```

### 7. Structured JSON Output

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "Extract product details from this image",
    "image_urls": ["https://example.com/product.jpg"],
    "json_schema": {
      "type": "object",
      "required": ["name", "price"],
      "properties": {
        "name": {"type": "string"},
        "price": {"type": "number"},
        "description": {"type": "string"}
      }
    }
  }'
```

**Response:**

```json
{
  "output": {
    "name": "Premium Headphones",
    "price": 299.99,
    "description": "Noise-cancelling wireless headphones"
  },
  "input_tokens": 1523,
  "output_tokens": 45,
  "total_tokens": 1568
}
```

## Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only security tests
pytest tests/test_security.py -v
```

### Security Scanning

```bash
# Static security analysis
bandit -r app/ -ll

# Check for known vulnerabilities
safety check
```

## Environment Variables (Deprecated - See Security Section Above)

| Variable           | Required | Default  | Description          |
| ------------------ | -------- | -------- | -------------------- |
| `GEMINI_API_KEY`   | ✅ Yes   | -        | Google AI API key    |

## Request Parameters

### Model Selection (`model`)

**Optional** - Choose which Gemini 3.0 model to use (default: `gemini-3-pro-preview`)

- **gemini-3-pro-preview** - Gemini 3 Pro with advanced reasoning (supports `LOW`, `HIGH` thinking levels)
- **gemini-3-flash-preview** - Gemini 3 Flash with speed and efficiency (supports `minimal`, `low`, `medium`, `high` thinking levels)

### Thinking Level (`thinking_level`)

**Optional** - Controls the depth of reasoning (default: `HIGH`)

**For Gemini 3 Pro:**
- **LOW** - Fast responses, basic reasoning
- **HIGH** - Maximum reasoning, slower but more thorough

**For Gemini 3 Flash:**
- **minimal** - Fastest, minimal reasoning (closest to "no thinking")
- **low** - Fast responses, basic reasoning
- **medium** - Balanced reasoning for most tasks
- **high** - Maximum reasoning, slower but more thorough

### Media Resolution (`media_resolution`)

**Optional** - Controls image/video processing quality (default: `MEDIUM`)

- **LOW** - Faster processing, lower detail
- **MEDIUM** - Balanced quality and speed (recommended)
- **HIGH** - Maximum detail, slower processing

## Project Structure

```
.
├── main.py              # FastAPI application entry point
├── app/                 # Main application package
│   ├── __init__.py      # Package initialization
│   ├── config.py        # Configuration and environment variables
│   ├── dependencies.py  # App dependencies and lifecycle
│   ├── models.py        # Pydantic data models
│   ├── security.py      # Security utilities (auth, SSRF protection)
│   ├── routes/          # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py    # Health check endpoint
│   │   └── generate.py  # Main generation endpoint
│   └── utils/           # Utility modules
│       ├── __init__.py
│       ├── prompts.py   # Prompt handling utilities
│       ├── images.py    # Image processing utilities
│       ├── schema.py    # JSON schema conversion
│       └── tokens.py    # Token counting utilities
├── tests/               # Test suite
│   ├── __init__.py
│   ├── conftest.py      # Test fixtures
│   ├── test_security.py # Security tests
│   └── test_api.py      # API endpoint tests
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container configuration
├── SECURITY.md          # Security policy and guidelines
├── .env                 # Environment variables (not in git)
└── .env.example         # Example environment variables
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid parameters, failed URL fetch, SSRF attempt)
- `403` - Forbidden (authentication failed)
- `422` - Validation error (invalid input data)
- `429` - Too many requests (rate limit exceeded)
- `500` - Server error (model failure, API issues)
- `503` - Service unavailable (health check failed)

Error response format:

```json
{
  "detail": "Error message here"
}
```

## Health Check

Check if the server is running:

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2024-03-20T10:00:00.123456",
  "uptime_seconds": 123.45,
  "model": "gemini-3-pro-preview",
  "version": "3.0.0"
}
```

## License

MIT

## Support

For API documentation and more details, visit:

- [Google AI Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- Interactive API docs: `http://localhost:8000/docs`
