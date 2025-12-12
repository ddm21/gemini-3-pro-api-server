# Gemini 3.0 Pro API Server

A FastAPI server that exposes Google's Gemini 3.0 Pro model as a REST API with support for flexible prompts (text/file URLs), image URLs, JSON schemas, and configurable thinking levels.

## Features

- ✅ Flexible prompts - Pass as text or load from URLs
- ✅ Multiple image support - Image URLs
- ✅ Structured JSON output - Use schemas for guaranteed structure
- ✅ Configurable thinking levels - LOW, MEDIUM, HIGH
- ✅ Dynamic system prompts - Control AI behavior per request

## Quick Start

### Local Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Create `.env` file:**

```env
GEMINI_API_KEY=your-api-key-here
THINKING_ENABLED=true
THINKING_LEVEL=HIGH
```

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
docker run -p 8000:8000 -e GEMINI_API_KEY=your-api-key-here gemini-api
```

Or with all environment variables:

```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-api-key-here \
  -e THINKING_ENABLED=true \
  -e THINKING_LEVEL=HIGH \
  gemini-api
```

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
  "json_schema": { ... } (optional)
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
  -d '{
    "user_prompt": "Write a haiku about coding"
  }'
```

### 2. With System Prompt

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
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

### 5. Structured JSON Output

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

## Environment Variables

| Variable           | Required | Default  | Options                 | Description          |
| ------------------ | -------- | -------- | ----------------------- | -------------------- |
| `GEMINI_API_KEY`   | ✅ Yes   | -        | Your API key            | Google AI API key    |
| `THINKING_ENABLED` | ❌ No    | `false`  | `true`, `false`         | Enable thinking mode |
| `THINKING_LEVEL`   | ❌ No    | `MEDIUM` | `LOW`, `MEDIUM`, `HIGH` | Reasoning depth      |

### Thinking Levels

- **LOW** - Fast responses, basic reasoning
- **MEDIUM** - Balanced speed and quality (recommended)
- **HIGH** - Maximum reasoning, slower but more thorough

## Project Structure

```
.
├── main.py              # FastAPI application entry point
├── app/                 # Main application package
│   ├── __init__.py      # Package initialization
│   ├── config.py        # Configuration and environment variables
│   ├── dependencies.py  # App dependencies and lifecycle
│   ├── models.py        # Pydantic data models
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
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container configuration
├── .env                 # Environment variables (not in git)
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid parameters, failed URL fetch)
- `500` - Server error (model failure, API issues)

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
  "thinking_enabled": true,
  "thinking_level": "HIGH",
  "version": "3.0.0"
}
```

## License

MIT

## Support

For API documentation and more details, visit:

- [Google AI Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- Interactive API docs: `http://localhost:8000/docs`
