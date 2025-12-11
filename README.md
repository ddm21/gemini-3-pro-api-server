# Gemini 3.0 Pro API Server

A FastAPI server that exposes Google's Gemini 3.0 Pro model as a REST API with support for structured JSON outputs via schemas, multiple image inputs, and configurable thinking levels.

## Features

- ✅ **Gemini 3.0 Pro** model with advanced reasoning
- ✅ **JSON Schema support** - Structured output validation when needed
- ✅ **Natural output** - AI decides format (JSON/Markdown/Text) based on context
- ✅ **Multiple image support** - Send multiple screenshots/images in one request
- ✅ **External system instructions** - Edit `system-instructions.md` without touching code
- ✅ **Configurable thinking levels** - LOW, MEDIUM, HIGH

## Quick Start

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file:

```env
GEMINI_API_KEY='your-api-key-here'
THINKING_ENABLED=true
THINKING_LEVEL=HIGH
```

3. Run the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Customizing System Instructions

Edit `system-instructions.md` to change the AI's role and behavior. Restart the server to apply changes.

## API Endpoint

### POST `/generate`

Generate responses with optional structured JSON output.

#### Request Body

```json
{
  "prompt": "Your prompt here",
  "json_schema": {},
  "image_urls": ["https://example.com/image1.png"]
}
```

**Parameters:**

| Parameter     | Type   | Required | Description                                              |
| ------------- | ------ | -------- | -------------------------------------------------------- |
| `prompt`      | string | ✅ Yes   | User's prompt                                            |
| `json_schema` | object | ❌ No    | JSON schema for structured output (enforces JSON format) |
| `image_urls`  | array  | ❌ No    | List of image URLs to analyze                            |
| `image_url`   | string | ❌ No    | Single image URL (backward compatible)                   |

#### Response

```json
{
  "output": {},
  "input_tokens": 1234,
  "output_tokens": 567,
  "total_tokens": 1801
}
```

**Note:** `output` can be a JSON object/array (when schema is provided or AI chooses JSON) or a string (markdown/text).

## Usage Examples

### 1. Natural Output (AI Decides Format)

The AI will choose the best format based on your prompt and system instructions.

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a review of this landing page",
    "image_urls": ["https://example.com/screenshot.png"]
  }'
```

**Response might be:**

- JSON if system instructions suggest structured data
- Markdown if writing a blog post
- Plain text for simple descriptions

### 2. Structured JSON with Schema

Enforce specific JSON structure with validation.

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Extract hero section details",
    "json_schema": {
      "type": "object",
      "required": ["headline", "cta"],
      "properties": {
        "headline": {"type": "string"},
        "subheadline": {"type": "string"},
        "cta_text": {"type": "string"}
      }
    },
    "image_urls": ["https://example.com/hero.png"]
  }'
```

**Response:**

```json
{
  "output": {
    "headline": "Build faster",
    "subheadline": "Ship in days, not weeks",
    "cta_text": "Get Started"
  },
  "input_tokens": 1234,
  "output_tokens": 56,
  "total_tokens": 1290
}
```

### 3. Multiple Images

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Compare desktop and mobile versions",
    "image_urls": [
      "https://example.com/desktop.png",
      "https://example.com/mobile.png"
    ]
  }'
```

### 4. Complex Schema Example

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Extract all pricing tiers",
    "json_schema": {
      "type": "object",
      "required": ["tiers"],
      "properties": {
        "tiers": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "price"],
            "properties": {
              "name": {"type": "string"},
              "price": {"type": "number"},
              "features": {
                "type": "array",
                "items": {"type": "string"}
              }
            }
          }
        }
      }
    },
    "image_urls": ["https://example.com/pricing.png"]
  }'
```

## How It Works

### Without JSON Schema

- AI outputs in whatever format makes sense
- System instructions guide the format
- Could be JSON, Markdown, or plain text
- Response parsing attempts JSON first, falls back to raw text

### With JSON Schema

- Forces `application/json` MIME type
- Validates output against schema
- Guarantees structured data
- Returns parsed JSON object/array

## Environment Variables

| Variable           | Default  | Options                 | Description                  |
| ------------------ | -------- | ----------------------- | ---------------------------- |
| `GEMINI_API_KEY`   | -        | Your API key            | Required: Google AI API key  |
| `THINKING_ENABLED` | `false`  | `true`, `false`         | Enable/disable thinking mode |
| `THINKING_LEVEL`   | `MEDIUM` | `LOW`, `MEDIUM`, `HIGH` | Reasoning depth              |

## Configuration

### Thinking Levels

- **LOW** - Fast responses, minimal reasoning
- **MEDIUM** - Balanced speed and quality (default)
- **HIGH** - Maximum reasoning capability, slower but more thorough

### Model Parameters

- **Model**: `gemini-3-pro-preview`
- **Temperature**: `0.6`
- **Top-p**: `0.4`
- **Max output tokens**: `12000`
- **Media resolution**: `MEDIUM`

## Use Cases

### 1. Flexible Content Generation

Let the AI choose the best format for blog posts, reviews, or descriptions.

### 2. Structured Data Extraction

Use JSON schemas to extract specific fields from images with guaranteed structure.

### 3. Multi-Image Analysis

Compare desktop vs mobile, or analyze multiple page sections.

### 4. Template Customization

The default system instructions are optimized for landing page analysis and template customization.

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid image URL, etc.)
- `500` - Server error (model failure, invalid response, etc.)

## Token Usage

Monitor token consumption in server logs:

```
[gemini-3-pro] mode=with_schema thinking=True level=HIGH tokens=2341/567/2908
[gemini-3-pro] mode=natural thinking=True level=HIGH tokens=1234/890/2124
```

## JSON Schema Format

Schemas follow standard JSON Schema format and are automatically converted to Gemini's `types.Schema` format:

```json
{
  "type": "object|array|string|number|boolean",
  "required": ["field1", "field2"],
  "properties": {
    "field1": {"type": "string"},
    "field2": {"type": "number"}
  },
  "items": {...},
  "description": "Optional description"
}
```

## License

MIT

## Support

For issues or questions, check the [Google AI documentation](https://ai.google.dev/gemini-api/docs).
