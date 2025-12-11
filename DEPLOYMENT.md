# Deploying to Easypanel

This guide shows you how to deploy the Gemini 3.0 Pro API Server to Easypanel.

## Prerequisites

- Easypanel account
- GitHub repository: https://github.com/ddm21/gemini-3-pro-api-server.git
- Gemini API key from Google AI Studio

## Deployment Steps

### 1. Create New App in Easypanel

1. Log in to your Easypanel dashboard
2. Click **"Create App"**
3. Choose **"GitHub"** as the source
4. Select your repository: `ddm21/gemini-3-pro-api-server`
5. Choose the `main` branch

### 2. Configure Build Settings

**Build Method:** Dockerfile

The Dockerfile is already included in the repository, so Easypanel will automatically detect it.

### 3. Set Environment Variables

In the Easypanel app settings, add these environment variables:

| Variable           | Value                      | Required                |
| ------------------ | -------------------------- | ----------------------- |
| `GEMINI_API_KEY`   | Your Gemini API key        | ✅ Yes                  |
| `THINKING_ENABLED` | `true` or `false`          | ❌ No (default: false)  |
| `THINKING_LEVEL`   | `LOW`, `MEDIUM`, or `HIGH` | ❌ No (default: MEDIUM) |

**Example:**

```
GEMINI_API_KEY=AIzaSyC...your-key-here
THINKING_ENABLED=true
THINKING_LEVEL=HIGH
```

### 4. Configure Port

**Port:** `8000`

Easypanel will automatically map this port to a public URL.

### 5. Deploy

1. Click **"Deploy"**
2. Wait for the build to complete (usually 1-2 minutes)
3. Your API will be available at: `https://your-app-name.easypanel.host`

## Testing Your Deployment

Once deployed, test your API:

```bash
curl -X POST "https://your-app-name.easypanel.host/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test prompt",
    "json_schema": {
      "type": "object",
      "properties": {
        "response": {"type": "string"}
      }
    }
  }'
```

## Updating Your Deployment

To update your deployment:

1. Push changes to your GitHub repository
2. Easypanel will automatically rebuild and redeploy (if auto-deploy is enabled)
3. Or manually trigger a rebuild in the Easypanel dashboard

## Resource Requirements

**Recommended:**

- **Memory:** 512MB - 1GB
- **CPU:** 0.5 - 1 vCPU

The app is lightweight and doesn't require much resources.

## Monitoring

Check logs in Easypanel dashboard:

- Look for: `[gemini-3-pro] mode=... thinking=... tokens=...`
- Monitor token usage to track API costs

## Custom Domain (Optional)

1. Go to your app settings in Easypanel
2. Click **"Domains"**
3. Add your custom domain
4. Update DNS records as instructed

## Troubleshooting

### Build Fails

- Check that Dockerfile is in the root directory
- Verify requirements.txt is present
- Check Easypanel build logs

### API Returns 500 Error

- Verify `GEMINI_API_KEY` is set correctly
- Check that `system-instructions.md` file exists
- Review application logs in Easypanel

### Slow Responses

- Consider increasing `THINKING_LEVEL` to `LOW` for faster responses
- Or disable thinking: `THINKING_ENABLED=false`

## Security Notes

- ✅ `.env` file is excluded via `.gitignore`
- ✅ API key is set via environment variables (not in code)
- ⚠️ Consider adding authentication for production use
- ⚠️ Monitor token usage to avoid unexpected costs

## Cost Considerations

- Easypanel hosting: ~$5-10/month (depending on plan)
- Gemini API: Pay per token (check Google AI pricing)
- Monitor usage in logs: `tokens=input/output/total`

## Support

- Easypanel docs: https://easypanel.io/docs
- GitHub repo: https://github.com/ddm21/gemini-3-pro-api-server
- Gemini API docs: https://ai.google.dev/gemini-api/docs
