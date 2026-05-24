# Deployment Guide
## AI Code Review Agent

**Complete deployment guide for development, staging, and production environments.**

---

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Railway Deployment](#railway-deployment-recommended)
4. [Render Deployment](#render-deployment)
5. [DigitalOcean Deployment](#digitalocean-deployment)
6. [AWS Deployment](#aws-deployment)
7. [Docker Deployment](#docker-deployment-self-hosted)
8. [Environment Configuration](#environment-configuration)
9. [Post-Deployment Tasks](#post-deployment-tasks)
10. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Deployment Overview

### Architecture Requirements

**Minimum Production Setup:**
- 1 FastAPI instance (2GB RAM, 2 vCPU)
- 2 Celery workers (2GB RAM each)
- 1 PostgreSQL database (4GB RAM, 20GB SSD)
- 1 Redis instance (1GB RAM)

**Estimated Monthly Cost:**
- **Railway:** $50-80/month
- **Render:** $60-90/month
- **DigitalOcean:** $70-100/month
- **AWS:** $80-120/month (with optimization)

---

## Pre-Deployment Checklist

### 1. Code Preparation

```bash
# Ensure all tests pass
poetry run pytest --cov=app

# Run linter
poetry run ruff check app/

# Type checking
poetry run mypy app/

# Security scan (optional)
poetry run bandit -r app/
```

### 2. Environment Secrets

Prepare the following API keys and secrets:

- [ ] GitHub App ID and Private Key
- [ ] GitHub Webhook Secret
- [ ] Anthropic API Key
- [ ] OpenAI API Key
- [ ] Pinecone API Key
- [ ] Database connection string
- [ ] Redis connection string
- [ ] Secret key for sessions

### 3. Database Migrations

```bash
# Ensure migrations are up to date
poetry run alembic upgrade head

# Create migration SQL for review
poetry run alembic upgrade head --sql > migration.sql
```

### 4. Docker Images

```bash
# Build and test Docker image locally
docker build -t ai-code-reviewer:latest .

# Test the image
docker run -p 8000:8000 ai-code-reviewer:latest

# Verify health endpoint
curl http://localhost:8000/health
```

---

## Railway Deployment (Recommended)

**Why Railway:** Simple setup, auto-scaling, integrated databases, free SSL, good for MVPs.

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Create new project

### Step 2: Deploy from GitHub

```bash
# Push code to GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main
```

**In Railway Dashboard:**
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Railway auto-detects Python and Dockerfile

### Step 3: Add Services

**Add PostgreSQL:**
1. Click "New Service" → "Database" → "PostgreSQL"
2. Railway automatically creates `DATABASE_URL` environment variable

**Add Redis:**
1. Click "New Service" → "Database" → "Redis"
2. Railway automatically creates `REDIS_URL` environment variable

### Step 4: Configure Environment Variables

In Railway dashboard, add variables:

```bash
# Application
APP_NAME=AI Code Reviewer
ENVIRONMENT=production
DEBUG=false

# GitHub App
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=/app/github-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=code-review-patterns

# Cost Controls
MAX_COST_PER_DAY_USD=10.00
MAX_REVIEWS_PER_HOUR=100

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://...  # Optional
```

**Upload GitHub Private Key:**
```bash
# Convert private key to base64
base64 -i github-app-key.pem -o github-key.b64

# Add as environment variable
GITHUB_PRIVATE_KEY=$(cat github-key.b64)
```

Then in your code, decode:
```python
import base64
import os

private_key = base64.b64decode(os.getenv("GITHUB_PRIVATE_KEY"))
```

### Step 5: Configure Services

**Create `railway.json` in project root:**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install poetry && poetry install --no-dev"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Add Celery Worker Service:**
1. Click "New Service" → "Empty Service"
2. Link to same GitHub repo
3. Set start command: `celery -A app.tasks.celery_app worker --loglevel=info`
4. Copy all environment variables from main app

### Step 6: Run Database Migrations

```bash
# SSH into Railway container
railway run bash

# Run migrations
alembic upgrade head
```

### Step 7: Deploy!

Railway automatically deploys on git push to main.

**Get your deployment URL:**
- Railway provides: `https://your-app-name.up.railway.app`
- Add custom domain in settings (optional)

**Update GitHub App webhook URL:**
- Go to GitHub App settings
- Update webhook URL to: `https://your-app-name.up.railway.app/api/webhooks/github`

---

## Render Deployment

**Why Render:** Good free tier, managed services, automatic SSL.

### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: Create Web Service

1. Dashboard → "New +" → "Web Service"
2. Connect GitHub repository
3. Configure:
   - **Name:** `ai-code-reviewer`
   - **Environment:** Python 3
   - **Build Command:** `pip install poetry && poetry install --no-dev`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add PostgreSQL

1. Dashboard → "New +" → "PostgreSQL"
2. Name: `ai-code-reviewer-db`
3. Plan: Free (or Starter for production)
4. Note the connection string

### Step 4: Add Redis

1. Dashboard → "New +" → "Redis"
2. Name: `ai-code-reviewer-redis`
3. Plan: Free (or Starter)
4. Note the connection string

### Step 5: Environment Variables

In web service settings → Environment:

```bash
DATABASE_URL=<from PostgreSQL service>
REDIS_URL=<from Redis service>

# Add all other variables from Railway section
GITHUB_APP_ID=...
ANTHROPIC_API_KEY=...
# etc.
```

### Step 6: Add Background Worker

1. Dashboard → "New +" → "Background Worker"
2. Connect to same repo
3. **Start Command:** `celery -A app.tasks.celery_app worker --loglevel=info`
4. Copy environment variables from web service

### Step 7: Deploy

Render auto-deploys on push to main branch.

**Access:**
- Your app: `https://ai-code-reviewer.onrender.com`

---

## DigitalOcean Deployment

**Why DigitalOcean:** Full control, predictable pricing, managed databases.

### Step 1: Create Droplet

```bash
# Create Ubuntu 22.04 droplet
# Size: 2GB RAM / 2 vCPU ($18/month)
```

**Via CLI:**
```bash
# Install doctl
brew install doctl

# Authenticate
doctl auth init

# Create droplet
doctl compute droplet create ai-reviewer \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-2gb \
  --region nyc1 \
  --ssh-keys <your-ssh-key-id>
```

### Step 2: Initial Server Setup

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create app user
useradd -m -s /bin/bash appuser
usermod -aG docker appuser
```

### Step 3: Setup Application

```bash
# Switch to app user
su - appuser

# Clone repository
git clone https://github.com/yourusername/ai-code-reviewer.git
cd ai-code-reviewer

# Create environment file
cp .env.example .env
nano .env  # Add production values
```

### Step 4: Setup Managed Database (Recommended)

**In DigitalOcean Dashboard:**
1. Create → Databases → PostgreSQL
2. Create → Databases → Redis
3. Copy connection strings to `.env`

**Or use Docker Compose for databases** (less recommended for production):
```yaml
# docker-compose.prod.yml already includes PostgreSQL and Redis
```

### Step 5: Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Run migrations
docker-compose exec app alembic upgrade head
```

### Step 6: Setup Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/ai-reviewer
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/ai-reviewer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Step 8: Setup Systemd Service (Auto-restart)

```bash
sudo nano /etc/systemd/system/ai-reviewer.service
```

**Service file:**
```ini
[Unit]
Description=AI Code Reviewer
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/appuser/ai-code-reviewer
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=appuser

[Install]
WantedBy=multi-user.target
```

**Enable service:**
```bash
sudo systemctl enable ai-reviewer
sudo systemctl start ai-reviewer
```

---

## AWS Deployment

**Why AWS:** Enterprise-grade, maximum flexibility, global availability.

### Architecture

```
Route 53 (DNS)
    ↓
Application Load Balancer
    ↓
ECS Fargate (FastAPI + Celery)
    ↓
RDS PostgreSQL + ElastiCache Redis
```

### Step 1: Setup VPC & Security Groups

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets (public and private)
# Create security groups
# Configure route tables
```

### Step 2: Setup RDS PostgreSQL

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name ai-reviewer-db-subnet \
  --subnet-ids subnet-xxx subnet-yyy

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier ai-reviewer-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username postgres \
  --master-user-password <secure-password> \
  --allocated-storage 20 \
  --db-subnet-group-name ai-reviewer-db-subnet
```

### Step 3: Setup ElastiCache Redis

```bash
# Create cache subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name ai-reviewer-cache-subnet \
  --subnet-ids subnet-xxx subnet-yyy

# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id ai-reviewer-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1 \
  --cache-subnet-group-name ai-reviewer-cache-subnet
```

### Step 4: Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name ai-code-reviewer

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -t ai-code-reviewer .
docker tag ai-code-reviewer:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-code-reviewer:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-code-reviewer:latest
```

### Step 5: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name ai-reviewer-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

**task-definition.json:**
```json
{
  "family": "ai-reviewer-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-code-reviewer:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-reviewer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Step 6: Create Load Balancer & Service

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name ai-reviewer-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create ECS service
aws ecs create-service \
  --cluster ai-reviewer-cluster \
  --service-name ai-reviewer-service \
  --task-definition ai-reviewer-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=app,containerPort=8000
```

---

## Docker Deployment (Self-Hosted)

**Complete docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: ai-code-reviewer:latest
    container_name: ai-reviewer-app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://reviewer:${DB_PASSWORD}@postgres:5432/code_reviewer
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    image: ai-code-reviewer:latest
    container_name: ai-reviewer-worker
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=postgresql://reviewer:${DB_PASSWORD}@postgres:5432/code_reviewer
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: ai-reviewer-postgres
    environment:
      POSTGRES_DB: code_reviewer
      POSTGRES_USER: reviewer
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U reviewer"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: ai-reviewer-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

---

## Environment Configuration

### Production Environment Variables

```bash
# Application
APP_NAME=AI Code Reviewer
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-secure-random-key>

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=50

# Celery
CELERY_BROKER_URL=redis://host:6379/0
CELERY_RESULT_BACKEND=redis://host:6379/1

# GitHub App
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=/app/github-app-key.pem
GITHUB_WEBHOOK_SECRET=<secure-random-string>

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_MAX_TOKENS=4096

OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Pinecone
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=code-review-patterns

# Cost Controls
MAX_REVIEWS_PER_HOUR=1000
MAX_COST_PER_DAY_USD=50.00

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring (Optional)
SENTRY_DSN=https://...
PROMETHEUS_ENABLED=true

# CORS
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## Post-Deployment Tasks

### 1. Run Database Migrations

```bash
# Railway
railway run alembic upgrade head

# Render
render run alembic upgrade head

# Docker
docker-compose exec app alembic upgrade head
```

### 2. Verify Health

```bash
curl https://your-domain.com/health

# Expected:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "ok"},
    "redis": {"status": "ok"},
    "celery": {"status": "ok"}
  }
}
```

### 3. Test Webhook

```bash
# Send test webhook
curl -X POST https://your-domain.com/api/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d @test_payload.json
```

### 4. Update GitHub App

1. Go to GitHub App settings
2. Update webhook URL to production domain
3. Test webhook delivery

### 5. Setup Monitoring

**Add Sentry (Error Tracking):**
```bash
# Install Sentry SDK
poetry add sentry-sdk

# In app/main.py
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
```

**Setup Uptime Monitoring:**
- Use UptimeRobot (free)
- Monitor: `https://your-domain.com/health`
- Alert on downtime

---

## Monitoring & Maintenance

### Health Checks

```bash
# Application health
curl https://your-domain.com/health

# Database health
curl https://your-domain.com/health/db

# Worker health
# Check Celery dashboard or logs
```

### Log Monitoring

```bash
# Railway
railway logs

# Render
render logs

# Docker
docker-compose logs -f app
docker-compose logs -f worker
```

### Performance Monitoring

**Key metrics to track:**
- Request rate (requests/second)
- Response time (P50, P95, P99)
- Error rate (4xx, 5xx)
- Queue depth (Celery)
- Database connections
- Memory usage
- CPU usage

### Backup Strategy

**Database backups:**
```bash
# Automated daily backups
# Railway: Automatic with plan
# Render: Automatic with Starter plan
# DigitalOcean: Configure automated backups

# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20240115.sql
```

### Scaling

**Horizontal scaling:**
```bash
# Railway: Increase instance count in dashboard
# Render: Increase instance count in settings
# Docker: Increase replicas
docker-compose up -d --scale worker=4
```

---

## Troubleshooting

### Issue: High latency

**Check:**
- Database slow queries
- Redis connection issues
- External API timeouts

**Solutions:**
- Add database indexes
- Increase cache TTL
- Add more workers

### Issue: Worker not processing

**Check:**
```bash
# View worker logs
docker-compose logs worker

# Check queue depth
docker-compose exec redis redis-cli LLEN celery
```

**Solutions:**
- Restart worker
- Increase worker count
- Check Redis connection

---

**Deployment complete! 🚀**

**Next steps:**
- Monitor performance
- Setup alerts
- Review logs regularly
- Plan scaling strategy
