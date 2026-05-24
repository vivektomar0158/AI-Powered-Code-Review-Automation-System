# Database Schema
## AI Code Review Agent

**Version:** 1.0  
**Author:** Vivek  
**Date:** January 2025  
**Database:** PostgreSQL 15+

---

## Table of Contents

1. [Overview](#overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Table Definitions](#table-definitions)
4. [Indexes & Performance](#indexes--performance)
5. [Constraints & Relationships](#constraints--relationships)
6. [Data Types & Conventions](#data-types--conventions)
7. [Migration Strategy](#migration-strategy)
8. [Vector Database Schema](#vector-database-schema)
9. [Sample Queries](#sample-queries)

---

## Overview

### Design Principles

1. **Normalization:** 3NF (Third Normal Form) for consistency
2. **Extensibility:** JSONB columns for flexible metadata
3. **Performance:** Strategic indexing for common queries
4. **Auditability:** Timestamps on all tables
5. **Referential Integrity:** Foreign keys with cascade rules

### Key Entities

- **repositories** - GitHub repositories being reviewed
- **pull_requests** - Pull requests within repositories
- **reviews** - Review sessions for each PR
- **comments** - Individual agent findings
- **patterns** - Learned code patterns from feedback
- **webhook_events** - Incoming GitHub events (audit trail)

### Storage Estimates

**For 1000 Reviews:**
- repositories: ~50 KB (100 repos × 0.5 KB)
- pull_requests: ~500 KB (1000 PRs × 0.5 KB)
- reviews: ~200 KB (1000 reviews × 0.2 KB)
- comments: ~5 MB (10,000 comments × 0.5 KB)
- patterns: ~2 MB (2000 patterns × 1 KB)
- webhook_events: ~10 MB (5000 events × 2 KB)

**Total:** ~18 MB for 1000 reviews  
**Projected 1 year (50K reviews):** ~900 MB

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│   repositories      │
│─────────────────────│
│ id (PK)             │
│ github_id (UNIQUE)  │
│ name                │
│ full_name           │
│ owner               │
│ config (JSONB)      │
│ is_active           │
│ created_at          │
│ updated_at          │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐        ┌─────────────────────┐
│   pull_requests     │        │  webhook_events     │
│─────────────────────│        │─────────────────────│
│ id (PK)             │        │ id (PK)             │
│ github_id (UNIQUE)  │        │ event_type          │
│ repository_id (FK)  │────┐   │ payload (JSONB)     │
│ number              │    │   │ signature           │
│ title               │    │   │ processed           │
│ author              │    │   │ created_at          │
│ state               │    │   └─────────────────────┘
│ base_branch         │    │
│ head_branch         │    │
│ diff_url            │    │
│ files_changed       │    │
│ additions           │    │
│ deletions           │    │
│ created_at          │    │
│ updated_at          │    │
└──────────┬──────────┘    │
           │               │
           │ 1:N           │
           │               │
           ▼               │
┌─────────────────────┐    │
│      reviews        │    │
│─────────────────────│    │
│ id (PK)             │    │
│ pull_request_id (FK)│────┘
│ status              │
│ total_issues        │
│ critical_issues     │
│ warnings            │
│ suggestions         │
│ processing_time_ms  │
│ cost_usd            │
│ agent_versions(JSON)│
│ created_at          │
│ completed_at        │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐        ┌─────────────────────┐
│     comments        │        │      patterns       │
│─────────────────────│        │─────────────────────│
│ id (PK)             │        │ id (PK)             │
│ review_id (FK)      │        │ repository_id (FK)  │───┐
│ github_comment_id   │        │ pattern_type        │   │
│ file_path           │        │ description         │   │
│ line_number         │        │ example_code        │   │
│ agent_type          │        │ vector_id           │───┼──> Pinecone
│ severity            │        │ positive_votes      │   │
│ message             │        │ negative_votes      │   │
│ code_snippet        │        │ language            │   │
│ suggestion          │        │ created_at          │   │
│ accepted            │        └─────────────────────┘   │
│ confidence_score    │                                  │
│ created_at          │                                  │
└─────────────────────┘                                  │
                                                         │
                    ┌────────────────────────────────────┘
                    │
                    ▼
            ┌───────────────────┐
            │  Pinecone Vector  │
            │      Database     │
            │───────────────────│
            │ Vector ID         │
            │ Embedding (1536D) │
            │ Metadata (JSON)   │
            └───────────────────┘
```

### Relationship Summary

- **repositories** ↔ **pull_requests**: One-to-Many
- **pull_requests** ↔ **reviews**: One-to-Many (multiple reviews per PR on updates)
- **reviews** ↔ **comments**: One-to-Many
- **repositories** ↔ **patterns**: One-to-Many
- **patterns** ↔ **Pinecone**: One-to-One (via vector_id)

---

## Table Definitions

### 1. repositories

Stores GitHub repositories that have the app installed.

```sql
CREATE TABLE repositories (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- GitHub Integration
    github_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(512) NOT NULL,  -- Format: "owner/repo-name"
    owner VARCHAR(255) NOT NULL,
    
    -- Configuration
    config JSONB DEFAULT '{}',  -- Parsed .ai-review.yml
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_full_name_format CHECK (full_name ~ '^[^/]+/[^/]+$')
);

-- Comments
COMMENT ON TABLE repositories IS 'GitHub repositories with AI review agent installed';
COMMENT ON COLUMN repositories.github_id IS 'GitHub internal repository ID';
COMMENT ON COLUMN repositories.config IS 'Repository-specific configuration from .ai-review.yml';
```

**Config JSONB Structure:**
```json
{
  "enabled": true,
  "agents": {
    "style": {"enabled": true, "severity_threshold": "warning"},
    "security": {"enabled": true},
    "performance": {"enabled": true},
    "bug": {"enabled": false}
  },
  "rules": {
    "max_function_length": 50,
    "exclude_paths": ["tests/", "*.min.js"]
  },
  "review_scope": "changed_files_only",
  "learning_enabled": true
}
```

---

### 2. pull_requests

Stores metadata for pull requests.

```sql
CREATE TABLE pull_requests (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- GitHub Integration
    github_id BIGINT UNIQUE NOT NULL,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- PR Details
    number INTEGER NOT NULL,  -- PR number (#42)
    title VARCHAR(512),
    author VARCHAR(255),
    state VARCHAR(50) NOT NULL,  -- open, closed, merged
    
    -- Branch Information
    base_branch VARCHAR(255),
    head_branch VARCHAR(255),
    
    -- Diff Details
    diff_url TEXT,
    files_changed INTEGER DEFAULT 0,
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_state CHECK (state IN ('open', 'closed', 'merged')),
    CONSTRAINT unique_repo_pr_number UNIQUE (repository_id, number)
);

-- Comments
COMMENT ON TABLE pull_requests IS 'Pull requests tracked for review';
COMMENT ON COLUMN pull_requests.github_id IS 'GitHub internal PR ID';
COMMENT ON COLUMN pull_requests.number IS 'PR number visible in GitHub (#42)';
```

---

### 3. reviews

Stores review session results.

```sql
CREATE TABLE reviews (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    pull_request_id INTEGER NOT NULL REFERENCES pull_requests(id) ON DELETE CASCADE,
    
    -- Review Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending: queued
    -- processing: agents running
    -- completed: successfully finished
    -- failed: error occurred
    -- partial: timeout, posted partial results
    
    -- Issue Summary
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    suggestions INTEGER DEFAULT 0,
    
    -- Performance Metrics
    processing_time_ms INTEGER,  -- Total time from start to finish
    cost_usd DECIMAL(10, 4),     -- API costs for this review
    
    -- Agent Metadata
    agent_versions JSONB,  -- Which agent versions executed
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT check_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial')),
    CONSTRAINT check_non_negative_issues CHECK (
        total_issues >= 0 AND 
        critical_issues >= 0 AND 
        warnings >= 0 AND 
        suggestions >= 0
    ),
    CONSTRAINT check_issue_sum CHECK (
        total_issues = critical_issues + warnings + suggestions
    )
);

-- Comments
COMMENT ON TABLE reviews IS 'Review sessions for pull requests';
COMMENT ON COLUMN reviews.agent_versions IS 'JSON: {"style": "1.0", "security": "1.2"}';
```

**agent_versions JSONB Example:**
```json
{
  "style": "1.0.0",
  "security": "1.2.0",
  "performance": "1.0.0",
  "bug": "1.1.0"
}
```

---

### 4. comments

Stores individual agent findings (issues raised).

```sql
CREATE TABLE comments (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    github_comment_id BIGINT,  -- GitHub's comment ID (if posted)
    
    -- Location
    file_path VARCHAR(1024),
    line_number INTEGER,
    
    -- Issue Classification
    agent_type VARCHAR(50) NOT NULL,  -- style, security, performance, bug
    severity VARCHAR(20) NOT NULL,     -- critical, warning, suggestion
    
    -- Issue Details
    message TEXT NOT NULL,
    code_snippet TEXT,       -- Problematic code
    suggestion TEXT,         -- Recommended fix
    
    -- Learning System
    accepted BOOLEAN,        -- Did developer implement suggestion?
    confidence_score DECIMAL(3, 2),  -- 0.00 to 1.00
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_agent_type CHECK (
        agent_type IN ('style', 'security', 'performance', 'bug', 'synthesizer')
    ),
    CONSTRAINT check_severity CHECK (
        severity IN ('critical', 'warning', 'suggestion')
    ),
    CONSTRAINT check_confidence_range CHECK (
        confidence_score >= 0.00 AND confidence_score <= 1.00
    )
);

-- Comments
COMMENT ON TABLE comments IS 'Individual issues found by agents';
COMMENT ON COLUMN comments.accepted IS 'NULL = pending, TRUE = dev fixed, FALSE = dev ignored';
```

---

### 5. patterns

Stores learned code patterns for the learning system.

```sql
CREATE TABLE patterns (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Pattern Classification
    pattern_type VARCHAR(50) NOT NULL,  -- style, security, performance, bug
    description TEXT,
    example_code TEXT,
    
    -- Vector Database Link
    vector_id VARCHAR(255) UNIQUE,  -- Pinecone vector ID
    
    -- Voting/Learning
    positive_votes INTEGER DEFAULT 0,  -- Times suggestion was accepted
    negative_votes INTEGER DEFAULT 0,  -- Times suggestion was rejected
    
    -- Language
    language VARCHAR(50),  -- python, javascript, java, etc.
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_pattern_type CHECK (
        pattern_type IN ('style', 'security', 'performance', 'bug')
    ),
    CONSTRAINT check_non_negative_votes CHECK (
        positive_votes >= 0 AND negative_votes >= 0
    )
);

-- Comments
COMMENT ON TABLE patterns IS 'Learned code patterns from review feedback';
COMMENT ON COLUMN patterns.vector_id IS 'Reference to Pinecone vector for similarity search';
```

---

### 6. webhook_events

Audit log of incoming GitHub webhooks.

```sql
CREATE TABLE webhook_events (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Event Details
    event_type VARCHAR(100) NOT NULL,  -- pull_request, pull_request_review, etc.
    payload JSONB NOT NULL,            -- Full GitHub webhook payload
    signature VARCHAR(255),             -- X-Hub-Signature-256 value
    
    -- Processing Status
    processed BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE webhook_events IS 'Audit log of GitHub webhook events';
COMMENT ON COLUMN webhook_events.payload IS 'Full JSON payload from GitHub';
```

**Retention Policy:**
- Keep for 30 days
- Automatic cleanup via cron job or pg_cron extension

---

## Indexes & Performance

### Primary Indexes

```sql
-- repositories
CREATE UNIQUE INDEX idx_repositories_github_id ON repositories(github_id);
CREATE INDEX idx_repositories_full_name ON repositories(full_name);
CREATE INDEX idx_repositories_active ON repositories(is_active) WHERE is_active = TRUE;

-- pull_requests
CREATE UNIQUE INDEX idx_pr_github_id ON pull_requests(github_id);
CREATE INDEX idx_pr_repository ON pull_requests(repository_id);
CREATE INDEX idx_pr_state ON pull_requests(state);
CREATE UNIQUE INDEX idx_pr_repo_number ON pull_requests(repository_id, number);
CREATE INDEX idx_pr_created_at ON pull_requests(created_at DESC);

-- reviews
CREATE INDEX idx_reviews_pr ON reviews(pull_request_id);
CREATE INDEX idx_reviews_status ON reviews(status);
CREATE INDEX idx_reviews_created_at ON reviews(created_at DESC);
CREATE INDEX idx_reviews_pr_latest ON reviews(pull_request_id, created_at DESC);

-- comments
CREATE INDEX idx_comments_review ON comments(review_id);
CREATE INDEX idx_comments_agent_severity ON comments(agent_type, severity);
CREATE INDEX idx_comments_accepted ON comments(accepted) WHERE accepted IS NOT NULL;
CREATE INDEX idx_comments_file_path ON comments(file_path);

-- patterns
CREATE INDEX idx_patterns_repository ON patterns(repository_id);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_language ON patterns(language);
CREATE UNIQUE INDEX idx_patterns_vector_id ON patterns(vector_id);
CREATE INDEX idx_patterns_votes ON patterns((positive_votes - negative_votes) DESC);

-- webhook_events
CREATE INDEX idx_webhooks_event_type ON webhook_events(event_type);
CREATE INDEX idx_webhooks_created_at ON webhook_events(created_at DESC);
CREATE INDEX idx_webhooks_processed ON webhook_events(processed) WHERE processed = FALSE;
```

### Composite Indexes for Common Queries

```sql
-- Get latest review for a PR
CREATE INDEX idx_reviews_pr_status_created 
ON reviews(pull_request_id, status, created_at DESC);

-- Analytics: Issues by agent and severity
CREATE INDEX idx_comments_review_agent_severity 
ON comments(review_id, agent_type, severity);

-- Pattern matching: Find patterns by repo and language
CREATE INDEX idx_patterns_repo_lang_type 
ON patterns(repository_id, language, pattern_type);
```

### Full-Text Search Index

For searching across comments:

```sql
-- Add tsvector column for full-text search
ALTER TABLE comments ADD COLUMN message_tsv tsvector;

-- Generate tsvector from message
UPDATE comments SET message_tsv = to_tsvector('english', message);

-- Create GIN index
CREATE INDEX idx_comments_message_fts ON comments USING GIN(message_tsv);

-- Auto-update trigger
CREATE TRIGGER comments_message_tsv_update BEFORE INSERT OR UPDATE
ON comments FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(message_tsv, 'pg_catalog.english', message);
```

**Usage:**
```sql
SELECT * FROM comments 
WHERE message_tsv @@ to_tsquery('english', 'sql & injection');
```

---

## Constraints & Relationships

### Foreign Key Relationships

```sql
-- pull_requests -> repositories
ALTER TABLE pull_requests
ADD CONSTRAINT fk_pr_repository
FOREIGN KEY (repository_id) 
REFERENCES repositories(id)
ON DELETE CASCADE;

-- reviews -> pull_requests
ALTER TABLE reviews
ADD CONSTRAINT fk_review_pr
FOREIGN KEY (pull_request_id)
REFERENCES pull_requests(id)
ON DELETE CASCADE;

-- comments -> reviews
ALTER TABLE comments
ADD CONSTRAINT fk_comment_review
FOREIGN KEY (review_id)
REFERENCES reviews(id)
ON DELETE CASCADE;

-- patterns -> repositories
ALTER TABLE patterns
ADD CONSTRAINT fk_pattern_repository
FOREIGN KEY (repository_id)
REFERENCES repositories(id)
ON DELETE CASCADE;
```

**Cascade Behavior:**
- Delete repository → Deletes all PRs, reviews, comments, patterns
- Delete PR → Deletes all reviews and comments
- Delete review → Deletes all comments

### Check Constraints

```sql
-- Ensure positive values
ALTER TABLE pull_requests
ADD CONSTRAINT check_positive_counts CHECK (
    files_changed >= 0 AND
    additions >= 0 AND
    deletions >= 0
);

-- Ensure completed_at is after created_at
ALTER TABLE reviews
ADD CONSTRAINT check_review_times CHECK (
    completed_at IS NULL OR completed_at >= created_at
);

-- Ensure line numbers are positive
ALTER TABLE comments
ADD CONSTRAINT check_positive_line CHECK (
    line_number IS NULL OR line_number > 0
);
```

---

## Data Types & Conventions

### Naming Conventions

- **Tables:** Plural, lowercase, underscores (`pull_requests`)
- **Columns:** Singular, lowercase, underscores (`created_at`)
- **Indexes:** `idx_{table}_{columns}` (`idx_pr_repository`)
- **Foreign Keys:** `fk_{from_table}_{to_table}` (`fk_pr_repository`)
- **Constraints:** `check_{table}_{description}` (`check_positive_counts`)

### Standard Columns

Every table includes:
- `id SERIAL PRIMARY KEY` - Auto-incrementing integer
- `created_at TIMESTAMP WITH TIME ZONE` - Record creation time
- `updated_at TIMESTAMP WITH TIME ZONE` (where applicable) - Last update time

### Timestamp Handling

**Auto-update trigger for updated_at:**

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables with updated_at
CREATE TRIGGER update_repositories_updated_at
    BEFORE UPDATE ON repositories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pull_requests_updated_at
    BEFORE UPDATE ON pull_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### JSONB Usage Guidelines

**When to use JSONB:**
- Configuration data (flexible schema)
- Metadata that varies by record
- Nested structures from external APIs

**When NOT to use JSONB:**
- Data requiring strict validation
- Frequently queried individual fields
- Critical business logic fields

**Querying JSONB:**
```sql
-- Check if agent is enabled
SELECT * FROM repositories
WHERE config->'agents'->'security'->>'enabled' = 'true';

-- Get all repos with max_function_length > 50
SELECT * FROM repositories
WHERE (config->'rules'->>'max_function_length')::INTEGER > 50;
```

---

## Migration Strategy

### Alembic Migrations

Using Alembic for version-controlled schema changes.

**Initial Migration (001_initial_schema.py):**
```python
"""Initial database schema

Revision ID: 001
Create Date: 2024-01-15
"""

def upgrade():
    # Create repositories table
    op.create_table(
        'repositories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('github_id', sa.BigInteger(), nullable=False),
        # ... rest of columns
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id')
    )
    
    # Create indexes
    op.create_index('idx_repositories_full_name', 'repositories', ['full_name'])
    # ... rest of migrations

def downgrade():
    # Reverse migration
    op.drop_table('repositories')
```

**Migration Workflow:**
```bash
# Create new migration
alembic revision --autogenerate -m "Add patterns table"

# Review generated migration
cat alembic/versions/002_add_patterns.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Data Migration Examples

**Backfill accepted status from code changes:**
```sql
-- Mark comments as accepted if developer changed the code
UPDATE comments c
SET accepted = TRUE
WHERE c.id IN (
    SELECT c.id
    FROM comments c
    JOIN reviews r ON c.review_id = r.id
    JOIN pull_requests pr ON r.pull_request_id = pr.id
    WHERE c.suggestion IS NOT NULL
    AND pr.state = 'merged'
    AND c.created_at < pr.updated_at
);
```

---

## Vector Database Schema

### Pinecone Configuration

**Index Setup:**
```python
import pinecone

pinecone.init(api_key="your-key", environment="us-east-1")

# Create index
pinecone.create_index(
    name="code-review-patterns",
    dimension=1536,  # OpenAI embedding size
    metric="cosine"
)
```

**Vector Metadata Schema:**
```json
{
  "pattern_id": 123,
  "repository_id": 5,
  "repository_name": "owner/repo",
  "pattern_type": "style",
  "language": "python",
  "accepted": true,
  "positive_votes": 12,
  "negative_votes": 3,
  "confidence": 0.92,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Querying:**
```python
# Generate embedding for new code
embedding = openai.Embedding.create(
    input="code snippet here",
    model="text-embedding-3-small"
)

# Search Pinecone
results = index.query(
    vector=embedding['data'][0]['embedding'],
    top_k=5,
    filter={
        "repository_id": 5,
        "language": "python",
        "accepted": True
    },
    include_metadata=True
)
```

### Sync Strategy PostgreSQL ↔ Pinecone

**When pattern is created:**
1. Insert into PostgreSQL `patterns` table
2. Generate embedding via OpenAI
3. Upsert to Pinecone with pattern.id as vector_id
4. Update PostgreSQL pattern.vector_id with Pinecone ID

**When pattern is deleted:**
1. Delete from Pinecone (use vector_id)
2. Delete from PostgreSQL

**Consistency Check:**
```sql
-- Find patterns missing vector_id
SELECT id, description 
FROM patterns 
WHERE vector_id IS NULL;

-- Find orphaned patterns (vector exists but pattern deleted)
-- Run periodic job to query Pinecone and cross-check
```

---

## Sample Queries

### Analytics Queries

**1. Average review time per repository:**
```sql
SELECT 
    r.full_name,
    COUNT(rev.id) as total_reviews,
    AVG(rev.processing_time_ms) / 1000.0 as avg_time_seconds,
    SUM(rev.cost_usd) as total_cost
FROM repositories r
JOIN pull_requests pr ON r.id = pr.repository_id
JOIN reviews rev ON pr.id = rev.pull_request_id
WHERE rev.status = 'completed'
GROUP BY r.id, r.full_name
ORDER BY total_reviews DESC;
```

**2. Issue distribution by severity and agent:**
```sql
SELECT 
    agent_type,
    severity,
    COUNT(*) as issue_count,
    AVG(confidence_score) as avg_confidence,
    SUM(CASE WHEN accepted = TRUE THEN 1 ELSE 0 END)::FLOAT / 
        NULLIF(COUNT(*) FILTER (WHERE accepted IS NOT NULL), 0) as acceptance_rate
FROM comments
GROUP BY agent_type, severity
ORDER BY agent_type, 
    CASE severity 
        WHEN 'critical' THEN 1 
        WHEN 'warning' THEN 2 
        WHEN 'suggestion' THEN 3 
    END;
```

**3. Top 10 most common issues:**
```sql
SELECT 
    LEFT(message, 100) as issue_preview,
    COUNT(*) as occurrences,
    agent_type,
    severity
FROM comments
GROUP BY LEFT(message, 100), agent_type, severity
ORDER BY occurrences DESC
LIMIT 10;
```

**4. Review performance over time:**
```sql
SELECT 
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as reviews,
    AVG(processing_time_ms) as avg_time_ms,
    AVG(total_issues) as avg_issues
FROM reviews
WHERE status = 'completed'
AND created_at > NOW() - INTERVAL '3 months'
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;
```

### Operational Queries

**5. Find stuck reviews (processing > 10 minutes):**
```sql
SELECT 
    rev.id,
    pr.number,
    r.full_name,
    rev.status,
    rev.created_at,
    EXTRACT(EPOCH FROM (NOW() - rev.created_at)) as age_seconds
FROM reviews rev
JOIN pull_requests pr ON rev.pull_request_id = pr.id
JOIN repositories r ON pr.repository_id = r.id
WHERE rev.status = 'processing'
AND rev.created_at < NOW() - INTERVAL '10 minutes'
ORDER BY rev.created_at;
```

**6. Unprocessed webhooks:**
```sql
SELECT 
    id,
    event_type,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) as age_seconds
FROM webhook_events
WHERE processed = FALSE
ORDER BY created_at;
```

**7. High-value patterns (frequently accepted):**
```sql
SELECT 
    p.id,
    p.pattern_type,
    p.language,
    p.description,
    p.positive_votes,
    p.negative_votes,
    (p.positive_votes::FLOAT / NULLIF(p.positive_votes + p.negative_votes, 0)) as acceptance_rate
FROM patterns p
WHERE p.positive_votes + p.negative_votes >= 5  -- Minimum sample size
ORDER BY acceptance_rate DESC, p.positive_votes DESC
LIMIT 20;
```

### Cleanup Queries

**8. Archive old webhook events:**
```sql
-- Create archive table
CREATE TABLE webhook_events_archive (LIKE webhook_events INCLUDING ALL);

-- Move old events
WITH moved AS (
    DELETE FROM webhook_events
    WHERE created_at < NOW() - INTERVAL '30 days'
    RETURNING *
)
INSERT INTO webhook_events_archive
SELECT * FROM moved;
```

**9. Delete orphaned patterns (no vector_id after 24 hours):**
```sql
DELETE FROM patterns
WHERE vector_id IS NULL
AND created_at < NOW() - INTERVAL '24 hours';
```

---

## Database Maintenance

### Vacuum & Analyze

```sql
-- Regular maintenance (run weekly)
VACUUM ANALYZE repositories;
VACUUM ANALYZE pull_requests;
VACUUM ANALYZE reviews;
VACUUM ANALYZE comments;

-- Full vacuum (run monthly, requires exclusive lock)
VACUUM FULL webhook_events;
```

### Table Partitioning (Future Optimization)

For high-volume tables like `comments` and `webhook_events`:

```sql
-- Partition comments by created_at (monthly)
CREATE TABLE comments_2024_01 PARTITION OF comments
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE comments_2024_02 PARTITION OF comments
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- etc.
```

### Backup Strategy

**Daily Backups:**
```bash
# Automated via pg_dump
pg_dump -h localhost -U reviewer -d code_reviewer \
  --format=custom \
  --file=backup_$(date +%Y%m%d).dump

# Retention: 7 daily, 4 weekly, 12 monthly
```

**Point-in-Time Recovery:**
- Enable WAL archiving
- Store WAL files in S3
- Can restore to any point within retention window

---

## Appendix

### SQL Script: Complete Schema Creation

```sql
-- Complete schema creation script
-- Run this to initialize database from scratch

BEGIN;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create tables (in order of dependencies)
-- (Full CREATE TABLE statements here)

-- Create indexes
-- (All index creation statements)

-- Create triggers
-- (Timestamp update triggers)

-- Insert default data
INSERT INTO repositories (github_id, name, full_name, owner, is_active)
VALUES (999999, 'test-repo', 'testuser/test-repo', 'testuser', FALSE);

COMMIT;
```

### Database Diagram Tools

**Generate ERD from existing database:**
```bash
# Using SchemaSpy
java -jar schemaspy.jar \
  -t pgsql \
  -db code_reviewer \
  -u reviewer \
  -p password \
  -host localhost \
  -o ./docs/schema

# Using pg_dump (schema only)
pg_dump -s code_reviewer > schema.sql
```

---

**Document Status:** ✅ Ready for Implementation  
**Database Version:** v1.0  
**Last Updated:** January 2025  
**Change Log:** Initial database schema design
