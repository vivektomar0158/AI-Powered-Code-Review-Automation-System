# Setup Guide
## AI Code Review Agent

**Complete installation and configuration guide from scratch to production.**

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Development Environment Setup](#development-environment-setup)
3. [GitHub App Configuration](#github-app-configuration)
4. [API Keys & Services](#api-keys--services)
5. [Database Setup](#database-setup)
6. [Application Configuration](#application-configuration)
7. [Running Locally](#running-locally)
8. [Verification & Testing](#verification--testing)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements

**Minimum (Development):**
- 4GB RAM
- 2 CPU cores
- 10GB disk space

**Recommended (Production):**
- 8GB RAM
- 4 CPU cores
- 20GB SSD storage

### Software Requirements

**Required:**
- Python 3.11 or higher
- Docker 20.10+ and Docker Compose 2.0+
- Git 2.30+
- PostgreSQL 15+ (via Docker or local)
- Redis 7+ (via Docker or local)

**Optional:**
- Poetry 1.7+ (recommended for dependency management)
- Node.js 18+ (for some tooling)
- ngrok or similar (for local webhook testing)

---

## Development Environment Setup

### Step 1: Install Python 3.11+

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Verify installation
python3.11 --version
```

**Linux (Ubuntu/Debian):**
```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Verify installation
python3.11 --version
```

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer, check "Add Python to PATH"
3. Verify: `python --version`

---

### Step 2: Install Docker

**macOS:**
```bash
# Download Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Or using Homebrew
brew install --cask docker

# Verify
docker --version
docker-compose --version
```

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker-compose --version
```

**Windows:**
- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

---

### Step 3: Install Poetry (Recommended)

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Verify
poetry --version

# Configure Poetry to create virtualenvs in project
poetry config virtualenvs.in-project true
```

**Alternative: Using pip**
```bash
pip install poetry
```

---

### Step 4: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-code-reviewer.git
cd ai-code-reviewer

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using Poetry
poetry install
poetry shell
```

---

## GitHub App Configuration

### Step 1: Create GitHub App

1. **Go to GitHub Settings**
   - Navigate to https://github.com/settings/apps
   - Click "New GitHub App"

2. **Basic Information**
   - **GitHub App name:** `AI Code Reviewer - Dev` (or your name)
   - **Homepage URL:** `http://localhost:8000` (temporary)
   - **Webhook URL:** `https://your-ngrok-url.ngrok.io/api/webhooks/github`
     - For local dev, use ngrok (see below)
   - **Webhook secret:** Generate random string
     ```bash
     openssl rand -hex 32
     ```
     Save this for later!

3. **Permissions**
   
   **Repository permissions:**
   - Pull requests: Read & Write
   - Contents: Read-only
   - Metadata: Read-only

   **Subscribe to events:**
   - [x] Pull request
   - [x] Pull request review
   - [x] Push (optional, for incremental reviews)

4. **Create App**
   - Click "Create GitHub App"
   - Note the **App ID** (you'll need this)

5. **Generate Private Key**
   - Scroll down to "Private keys"
   - Click "Generate a private key"
   - Download the `.pem` file
   - Save it to your project directory as `github-app-key.pem`
   - **IMPORTANT:** Add to `.gitignore` (never commit this!)

6. **Install App**
   - Click "Install App" in left sidebar
   - Select repositories to install on
   - For testing, select a test repository

---

### Step 2: Setup ngrok (Local Development)

ngrok creates a public URL for your local server to receive webhooks.

```bash
# Install ngrok
# macOS
brew install ngrok

# Linux
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin

# Sign up and get auth token at https://dashboard.ngrok.com
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start ngrok tunnel
ngrok http 8000
```

**Output:**
```
Forwarding  https://abc123def.ngrok.io -> http://localhost:8000
```

**Update GitHub App webhook URL:**
- Go to your GitHub App settings
- Update webhook URL to: `https://abc123def.ngrok.io/api/webhooks/github`

---

## API Keys & Services

### Step 1: Anthropic (Claude API)

1. **Sign up:** https://console.anthropic.com/
2. **Get API key:**
   - Go to Settings → API Keys
   - Click "Create Key"
   - Copy the key (starts with `sk-ant-`)
3. **Add credits:** $5-10 is enough for development

---

### Step 2: OpenAI (Embeddings)

1. **Sign up:** https://platform.openai.com/
2. **Get API key:**
   - Go to API keys section
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)
3. **Add credits:** $5 is enough for development

---

### Step 3: Pinecone (Vector Database)

1. **Sign up:** https://www.pinecone.io/
2. **Create index:**
   - Click "Create Index"
   - **Name:** `code-review-patterns`
   - **Dimensions:** `1536` (OpenAI embedding size)
   - **Metric:** `cosine`
   - **Environment:** Choose free tier region
3. **Get API key:**
   - Go to API Keys section
   - Copy the API key
4. **Get environment:** Note the environment name (e.g., `us-east-1-aws`)

---

## Database Setup

### Option A: Using Docker (Recommended)

```bash
# Navigate to docker directory
cd docker

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps

# Check PostgreSQL
docker-compose exec postgres psql -U reviewer -d code_reviewer -c "SELECT version();"

# Check Redis
docker-compose exec redis redis-cli ping
# Should return: PONG
```

---

### Option B: Local Installation

**PostgreSQL:**
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb code_reviewer

# Linux
sudo apt install postgresql-15
sudo systemctl start postgresql
sudo -u postgres createdb code_reviewer
```

**Redis:**
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
sudo systemctl start redis
```

---

### Step 3: Run Database Migrations

```bash
# From project root
cd ..

# Run migrations using Alembic
poetry run alembic upgrade head

# Verify tables created
docker-compose exec postgres psql -U reviewer -d code_reviewer -c "\dt"
```

**Expected output:**
```
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+---------
 public | repositories    | table | reviewer
 public | pull_requests   | table | reviewer
 public | reviews         | table | reviewer
 public | comments        | table | reviewer
 public | patterns        | table | reviewer
 public | webhook_events  | table | reviewer
```

---

## Application Configuration

### Step 1: Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

### Step 2: Fill in Required Values

**`.env` file:**
```bash
# Application
APP_NAME="AI Code Reviewer"
DEBUG=true
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database (if using Docker Compose, these are correct)
DATABASE_URL=postgresql://reviewer:password@localhost:5432/code_reviewer
REDIS_URL=redis://localhost:6379/0

# GitHub App (from GitHub App setup)
GITHUB_APP_ID=123456                        # Your App ID
GITHUB_PRIVATE_KEY_PATH=./github-app-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret   # Generated earlier

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-api03-...          # From Anthropic console
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...                       # From OpenAI platform
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Pinecone
PINECONE_API_KEY=your-pinecone-key          # From Pinecone
PINECONE_ENVIRONMENT=us-east-1              # Your Pinecone environment
PINECONE_INDEX_NAME=code-review-patterns

# Cost Controls
MAX_REVIEWS_PER_HOUR=100
MAX_COST_PER_DAY_USD=10.00

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

### Step 3: Verify Configuration

```bash
# Test configuration loading
poetry run python -c "from app.core.config import settings; print(settings.dict())"
```

Should print your configuration without errors.

---

## Running Locally

### Step 1: Start Infrastructure Services

```bash
# Start PostgreSQL and Redis (if using Docker)
cd docker
docker-compose up -d

# Verify
docker-compose ps
```

---

### Step 2: Start Application

**Terminal 1: FastAPI Server**
```bash
# From project root
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Terminal 2: Celery Worker**
```bash
poetry run celery -A app.tasks.celery_app worker --loglevel=info
```

**Expected output:**
```
 -------------- celery@hostname v5.3.0
---- **** -----
--- * ***  * -- [Configuration]
-- * - **** ---
- ** ---------- .> app:         app.tasks:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- *** --- * --- .> results:     redis://localhost:6379/1
-- ******* ----
--- ***** -----
 -------------- [Queues]
                .> reviews
                .> analytics

[tasks]
  . app.tasks.review_tasks.process_pr_review
  . app.tasks.analytics.compute_metrics

[2024-01-15 10:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-01-15 10:00:00,000: INFO/MainProcess] celery@hostname ready.
```

**Terminal 3: ngrok (for webhooks)**
```bash
ngrok http 8000
```

---

### Step 3: Verify API is Running

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"},
    "celery": {"status": "ok"}
  }
}

# API documentation
open http://localhost:8000/docs
```

---

## Verification & Testing

### Test 1: Manual Webhook Trigger

```bash
# Create test webhook payload
cat > test_webhook.json <<EOF
{
  "action": "opened",
  "number": 1,
  "pull_request": {
    "id": 123456,
    "number": 1,
    "state": "open",
    "title": "Test PR",
    "user": {"login": "testuser"},
    "head": {"ref": "test-branch", "sha": "abc123"},
    "base": {"ref": "main", "sha": "def456"}
  },
  "repository": {
    "id": 789,
    "name": "test-repo",
    "full_name": "user/test-repo"
  }
}
EOF

# Calculate HMAC signature
WEBHOOK_SECRET="your-webhook-secret"
SIGNATURE=$(echo -n "$(cat test_webhook.json)" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | cut -d' ' -f2)

# Send webhook
curl -X POST http://localhost:8000/api/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -d @test_webhook.json

# Expected response:
{
  "status": "accepted",
  "message": "Webhook received, review queued"
}
```

---

### Test 2: Check Celery Logs

After sending webhook, check Terminal 2 (Celery worker) for:

```
[2024-01-15 10:05:00,000: INFO/MainProcess] Task app.tasks.review_tasks.process_pr_review received
[2024-01-15 10:05:00,100: INFO/Worker-1] Starting review for PR #1
[2024-01-15 10:05:05,000: INFO/Worker-1] Review completed: 12 issues found
[2024-01-15 10:05:05,100: INFO/MainProcess] Task app.tasks.review_tasks.process_pr_review succeeded
```

---

### Test 3: Run Unit Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

**Expected output:**
```
==================== test session starts ====================
collected 45 items

tests/test_api/test_webhooks.py ......          [ 13%]
tests/test_agents/test_style_agent.py .....     [ 24%]
tests/test_services/test_github.py .......      [ 40%]
...

==================== 45 passed in 12.34s ====================
```

---

### Test 4: Create Real PR

1. **Install GitHub App** on test repository
2. **Create branch:**
   ```bash
   git checkout -b test-review
   ```

3. **Add code with intentional issues:**
   ```python
   # test_file.py
   def login(username, password):
       # SQL injection vulnerability
       query = f"SELECT * FROM users WHERE name='{username}'"
       
       # Function too long (add 60+ lines of code here)
       ...
   ```

4. **Push and create PR:**
   ```bash
   git add test_file.py
   git commit -m "Add login function"
   git push origin test-review
   ```

5. **Open PR on GitHub**

6. **Watch for review comment** (should appear in ~30-60 seconds)

---

## Troubleshooting

### Issue 1: "Connection to database failed"

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection string in .env
echo $DATABASE_URL

# Test connection manually
docker-compose exec postgres psql -U reviewer -d code_reviewer

# Restart database
docker-compose restart postgres
```

---

### Issue 2: "Redis connection refused"

**Symptoms:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Solutions:**
```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

---

### Issue 3: "Webhook signature verification failed"

**Symptoms:**
```
401 Unauthorized: Invalid webhook signature
```

**Solutions:**
```bash
# Verify webhook secret matches in:
# 1. GitHub App settings
# 2. .env file (GITHUB_WEBHOOK_SECRET)

# Check signature calculation
# The secret must be identical in both places
```

---

### Issue 4: "Anthropic API key invalid"

**Symptoms:**
```
anthropic.AuthenticationError: Invalid API key
```

**Solutions:**
```bash
# Verify API key in .env
echo $ANTHROPIC_API_KEY

# Test API key directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'

# Generate new key if needed at console.anthropic.com
```

---

### Issue 5: "Celery worker not processing jobs"

**Symptoms:**
- Webhook received but no review posted
- Celery logs show "ready" but no tasks

**Solutions:**
```bash
# Check Celery connection to Redis
# In Celery terminal, should see:
# "Connected to redis://localhost:6379/0"

# Check queue depth
docker-compose exec redis redis-cli
> LLEN celery

# Manually trigger a task
poetry run python -c "from app.tasks.review_tasks import process_pr_review; process_pr_review.delay(1)"

# Restart worker
# Ctrl+C in Terminal 2, then restart:
poetry run celery -A app.tasks.celery_app worker --loglevel=info
```

---

### Issue 6: "Ngrok tunnel expired"

**Symptoms:**
- Webhooks worked before, now failing
- GitHub webhook shows delivery failures

**Solutions:**
```bash
# Free ngrok tunnels expire after 2 hours
# Restart ngrok
ngrok http 8000

# Update GitHub App webhook URL with new ngrok URL
# Go to: https://github.com/settings/apps/your-app
# Update webhook URL to new ngrok address
```

**Alternative for persistent URL:**
- Upgrade to ngrok paid plan ($8/month)
- Or deploy to cloud (Railway, Render) for permanent URL

---

### Issue 7: "Import errors / Module not found"

**Symptoms:**
```
ModuleNotFoundError: No module named 'app'
```

**Solutions:**
```bash
# Ensure virtual environment is activated
poetry shell

# Or using venv:
source venv/bin/activate

# Reinstall dependencies
poetry install

# Verify Python version
python --version  # Should be 3.11+

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Next Steps

After successful setup:

1. ✅ **Read the architecture docs:** [docs/architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
2. ✅ **Review API documentation:** [docs/planning/API_SPECIFICATION.md](../planning/API_SPECIFICATION.md)
3. ✅ **Check agent design:** [docs/architecture/AGENT_DESIGN.md](../architecture/AGENT_DESIGN.md)
4. ✅ **Start development:** See [DEVELOPMENT.md](DEVELOPMENT.md)
5. ✅ **Deploy to production:** See [DEPLOYMENT.md](../operations/DEPLOYMENT.md)

---

## Getting Help

**Common Issues:**
- Check [Troubleshooting](#troubleshooting) section above
- Review [GitHub Issues](https://github.com/yourusername/ai-code-reviewer/issues)

**Support:**
- 📧 Email: your.email@example.com
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/ai-code-reviewer/discussions)
- 🐛 Bugs: [GitHub Issues](https://github.com/yourusername/ai-code-reviewer/issues)

---

**Setup complete! 🎉**

**Ready to start reviewing code with AI!**
