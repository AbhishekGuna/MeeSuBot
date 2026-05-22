# Railway Deployment Guide for MeeSuBot

## Step 1: Prepare Your GitHub Repository

Make sure your code is pushed to GitHub:
```bash
git add Dockerfile .dockerignore docker-compose.yml .env.example
git commit -m "Add Docker configuration for Railway deployment"
git push origin main
```

## Step 2: Create Railway Account & Project

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Create a new project: **"New Project" → "Deploy from GitHub repo"**
4. Select your `MeeSuBot` repository

## Step 3: Add PostgreSQL Database

1. In your Railway project dashboard, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically provision PostgreSQL
4. The `DATABASE_URL` will be available as an environment variable

## Step 4: Configure Environment Variables

In Railway project dashboard:
1. Go to **"Variables"** tab
2. Add your secrets:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `DATABASE_URL`: Will be auto-detected from PostgreSQL service

Example:
```
DISCORD_TOKEN = your_token_here
GEMINI_API_KEY = your_key_here
```

## Step 5: Deploy

Railway will automatically:
1. Detect the Dockerfile
2. Build the Docker image
3. Deploy the container
4. Keep it running 24/7

**That's it!** Your bot is now live.

## Step 6: Monitor & Debug

- View **Logs**: Click on the service → "Logs" tab to see bot output
- View **Metrics**: Monitor CPU, memory, and network usage
- Redeploy: Push to GitHub → automatic redeployment

## Troubleshooting

### Bot shows "Error" status
- Check logs for errors
- Verify environment variables are set correctly
- Ensure Discord token is valid

### Database connection fails
- Verify PostgreSQL is connected (should appear in "Services" list)
- Check `DATABASE_URL` is correct
- Database initialization happens automatically on first run

### Bot not responding
- Check bot is online in Railway logs
- Verify Discord token hasn't expired
- Ensure bot has permissions in your server

## Local Testing (Optional)

Test locally before deploying:
```bash
# Copy .env.example to .env and fill in your tokens
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start locally
python -m __main__

# Or with Docker:
docker-compose up
```

## Cost

Railway offers **$5/month free credit**, which typically covers:
- 1 Discord bot running 24/7
- 1 PostgreSQL database (small)
- ~2-3 months before credit runs out

After free credit, pricing is pay-as-you-go (~$0.07/GB memory/hour).

## Support

- Railway Docs: https://docs.railway.app
- Discord.py Docs: https://discordpy.readthedocs.io
- For issues: Check Railway logs or open a GitHub issue
