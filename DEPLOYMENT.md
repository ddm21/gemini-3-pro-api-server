# Deployment & Docker Guide

## Docker Deployment

### Building the Image

```bash
docker build -t gemini-api .
```

### Running the Container

**Basic (with API key only):**

```bash
docker run -p 8000:8000 -e GEMINI_API_KEY=your-api-key-here gemini-api
```

**With all options:**

```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-api-key-here \
  -e THINKING_ENABLED=true \
  -e THINKING_LEVEL=HIGH \
  gemini-api
```

**With environment file:**

```bash
docker run -p 8000:8000 --env-file .env gemini-api
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  gemini-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - THINKING_ENABLED=true
      - THINKING_LEVEL=HIGH
    restart: unless-stopped
```

Run with:

```bash
docker-compose up -d
```

## Cloud Deployment

### Deploy to any platform that supports Docker:

- **Google Cloud Run**
- **AWS ECS/Fargate**
- **Azure Container Instances**
- **DigitalOcean App Platform**
- **Railway**
- **Render**

### Example: Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/gemini-api

# Deploy to Cloud Run
gcloud run deploy gemini-api \
  --image gcr.io/YOUR_PROJECT_ID/gemini-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-api-key-here,THINKING_ENABLED=true,THINKING_LEVEL=HIGH
```

## Files Included in Docker Image

The Dockerfile copies the following files:

- `main.py` - FastAPI application entry point
- `config.py` - Configuration management
- `dependencies.py` - App lifecycle and dependencies
- `models.py` - Data models
- `routes/` - All route handlers (health, generate)
- `utils/` - All utility modules (prompts, images, schema, tokens)

## Files Excluded (.dockerignore)

The following are automatically excluded:

- `__pycache__/` and compiled Python files
- `.env` and environment files (pass via `-e` flags instead)
- Test files (`test_*.py`)
- Documentation files (`.md`)
- IDE and Git files

## Health Check

Once deployed, verify the service is running:

```bash
curl https://your-deployment-url.com/health
```

## Production Recommendations

1. **Use secrets management** for `GEMINI_API_KEY` instead of environment variables
2. **Enable rate limiting** if exposing publicly
3. **Add authentication** (API keys, OAuth, etc.)
4. **Monitor token usage** to control costs
5. **Set up logging** and error tracking (Sentry, etc.)
6. **Configure CORS** appropriately in `main.py` (currently set to allow all origins)
