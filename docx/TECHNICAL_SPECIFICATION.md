# Technical Specification
## AI Code Review Agent

**Version:** 1.0  
**Author:** Vivek  
**Date:** January 2025  
**Status:** Design Phase

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Component Design](#component-design)
5. [Data Models](#data-models)
6. [API Design](#api-design)
7. [Multi-Agent System](#multi-agent-system)
8. [Learning System](#learning-system)
9. [Performance & Scalability](#performance--scalability)
10. [Security](#security)
11. [Deployment](#deployment)
12. [Monitoring & Observability](#monitoring--observability)

---

## System Overview

### High-Level Architecture

The AI Code Review Agent is a distributed, event-driven system that automatically reviews GitHub pull requests using multiple specialized AI agents. The system follows a microservices-inspired architecture with clear separation between webhook handling, async processing, AI orchestration, and data persistence.

### Key Design Principles

1. **Event-Driven:** Reacts to GitHub webhook events asynchronously
2. **Modular Agents:** Each agent specializes in one review aspect (single responsibility)
3. **Learning-First:** System improves accuracy through feedback loops
4. **Cost-Conscious:** Caching and optimization to minimize API costs
5. **Fail-Safe:** Graceful degradation, partial results better than no results
6. **Observable:** Comprehensive logging and metrics for debugging

### System Boundaries

**In Scope:**
- Receiving and validating GitHub webhooks
- Fetching PR data via GitHub API
- Multi-agent code analysis using LLMs
- Posting review comments back to GitHub
- Storing review history and patterns
- Learning from developer feedback

**Out of Scope:**
- Running actual code or tests (static analysis only)
- Merging or approving PRs automatically
- Real-time collaboration features
- Non-GitHub platforms

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Platform                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Developer│───▶│   PR     │───▶│ Webhooks │                  │
│  │  Creates │    │ Created  │    │  Fired   │                  │
│  └──────────┘    └──────────┘    └────┬─────┘                  │
└───────────────────────────────────────┼──────────────────────────┘
                                        │ HTTPS POST
                                        │ (webhook payload)
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI Review System (FastAPI)                  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Layer (FastAPI)                          │  │
│  │  ┌────────────┐  ┌───────────┐  ┌────────────┐          │  │
│  │  │ Webhook    │  │  Review   │  │ Analytics  │          │  │
│  │  │ Receiver   │  │    API    │  │    API     │          │  │
│  │  └─────┬──────┘  └───────────┘  └────────────┘          │  │
│  └────────┼─────────────────────────────────────────────────┘  │
│           │ Validate signature                                  │
│           │ Deduplicate event                                   │
│           ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Redis Queue & Cache                          │  │
│  │  ┌────────────────┐  ┌──────────────┐                    │  │
│  │  │  Job Queue     │  │ Deduplication│                    │  │
│  │  │  (Celery)      │  │    Cache     │                    │  │
│  │  └───────┬────────┘  └──────────────┘                    │  │
│  └──────────┼───────────────────────────────────────────────┘  │
│             │ Async job pickup                                  │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Background Workers (Celery)                     │  │
│  │  ┌─────────────────────────────────────────┐             │  │
│  │  │      Review Orchestrator                │             │  │
│  │  │  - Fetches PR data from GitHub          │             │  │
│  │  │  - Parses diffs into file chunks        │             │  │
│  │  │  - Coordinates multi-agent review       │             │  │
│  │  │  - Posts results back to GitHub         │             │  │
│  │  └──────────────┬──────────────────────────┘             │  │
│  └─────────────────┼────────────────────────────────────────┘  │
│                    │ Invokes agent graph                        │
│                    ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Multi-Agent System (LangGraph)                    │  │
│  │                                                            │  │
│  │    ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │    │  Style   │  │ Security │  │Performance│             │  │
│  │    │  Agent   │  │  Agent   │  │  Agent   │             │  │
│  │    └────┬─────┘  └────┬─────┘  └────┬─────┘             │  │
│  │         │             │             │                     │  │
│  │         └─────────────┼─────────────┘                     │  │
│  │                       ▼                                    │  │
│  │              ┌─────────────────┐                          │  │
│  │              │  Bug Detector   │                          │  │
│  │              │     Agent       │                          │  │
│  │              └────────┬────────┘                          │  │
│  │                       │                                    │  │
│  │                       ▼                                    │  │
│  │              ┌─────────────────┐                          │  │
│  │              │  Synthesizer    │                          │  │
│  │              │  - Deduplicates │                          │  │
│  │              │  - Prioritizes  │                          │  │
│  │              │  - Formats      │                          │  │
│  │              └────────┬────────┘                          │  │
│  └───────────────────────┼───────────────────────────────────┘  │
│                          │ Final review                          │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         External Services Integration                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│  │  │ Claude   │  │ OpenAI   │  │ Pinecone │               │  │
│  │  │   API    │  │Embeddings│  │  Vector  │               │  │
│  │  │ (Review) │  │          │  │    DB    │               │  │
│  │  └──────────┘  └──────────┘  └──────────┘               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Data Layer                                   │  │
│  │  ┌────────────────┐  ┌──────────────┐                    │  │
│  │  │  PostgreSQL    │  │    Redis     │                    │  │
│  │  │  - PRs         │  │  - Cache     │                    │  │
│  │  │  - Reviews     │  │  - Sessions  │                    │  │
│  │  │  - Patterns    │  │  - Counters  │                    │  │
│  │  └────────────────┘  └──────────────┘                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Component Interactions

**Flow 1: PR Created (Webhook → Review)**
```
GitHub → FastAPI Webhook Endpoint → Redis Deduplication → Celery Queue
→ Review Orchestrator → GitHub API (fetch PR) → LangGraph Multi-Agent
→ 4 Agents Run in Parallel → Synthesizer Combines → PostgreSQL (store)
→ GitHub API (post comment) → Done (45-60 seconds total)
```

**Flow 2: Learning from Feedback**
```
Developer edits code → Review Orchestrator detects acceptance
→ Embedding Service (OpenAI) → Vector stored in Pinecone
→ Future PR → Pattern Matcher queries Pinecone → Influences review
```

---

## Technology Stack

### Backend Framework

**FastAPI 0.110+**
- **Why:** Native async support, automatic OpenAPI docs, Pydantic validation
- **Alternatives Considered:** Flask (no async), Django (too heavy)
- **Decision:** FastAPI's async capabilities critical for handling webhooks efficiently

### Database Layer

**PostgreSQL 15+**
- **Why:** JSONB support for flexible PR metadata, full-text search, ACID guarantees
- **Usage:** Store PRs, reviews, comments, repository configs
- **Schema:** Normalized relational design with JSONB for extensibility

**Pinecone Vector Database**
- **Why:** Managed vector search, 1M free vectors, simple API
- **Usage:** Store code pattern embeddings for learning system
- **Alternative:** Weaviate (self-hosted, more complex setup)

**Redis 7**
- **Why:** Fast in-memory operations, built-in pub/sub, persistence
- **Usage:** Webhook deduplication, Celery broker, caching, rate limiting

### AI & Agent Framework

**Anthropic Claude Sonnet 4.5**
- **Why:** Best-in-class code understanding, 200K context window, structured outputs
- **Cost:** $3/M input tokens, $15/M output tokens
- **Usage:** All four agents use Claude for analysis

**LangGraph 0.2+**
- **Why:** Built for multi-agent coordination, state management, conditional flows
- **Alternative:** LangChain (less control), custom orchestration (more work)
- **Decision:** LangGraph's graph-based state machine perfect for our agent workflow

**OpenAI text-embedding-3-small**
- **Why:** High-quality embeddings at low cost ($0.02/M tokens)
- **Usage:** Generate vectors for code patterns
- **Alternative:** Sentence-transformers (free but slower, local)

### Background Processing

**Celery 5.3+ with Redis**
- **Why:** Battle-tested, supports retries, priority queues, monitoring
- **Usage:** Async PR review processing
- **Alternative:** FastAPI BackgroundTasks (too simple for our needs)

### GitHub Integration

**PyGithub 2.3+**
- **Why:** Comprehensive GitHub API wrapper, active maintenance
- **Usage:** Fetch PR data, post comments, manage webhooks

### Infrastructure

**Docker & Docker Compose**
- **Why:** Consistent environments, easy local development
- **Usage:** Containerize app, PostgreSQL, Redis, Celery workers

**GitHub Actions**
- **Why:** Native CI/CD for GitHub projects, free for public repos
- **Usage:** Run tests on PR, deploy on merge to main

### Development Tools

**Poetry**
- **Why:** Better dependency resolution than pip, lockfile support
- **Usage:** Manage Python packages and virtual environments

**Ruff**
- **Why:** 10-100x faster than flake8/black, all-in-one linter+formatter
- **Usage:** Code quality checks in pre-commit hooks

**pytest**
- **Why:** Industry standard, extensive plugin ecosystem
- **Usage:** Unit tests, integration tests, coverage reporting

---

## Component Design

### 1. Webhook Receiver

**Responsibility:** Receive and validate GitHub webhook events

**Key Functions:**
- Validate HMAC signature using webhook secret
- Parse webhook payload into Pydantic models
- Check Redis for duplicate events (GitHub can send duplicates)
- Enqueue review job to Celery

**Error Handling:**
- Invalid signature → Return 401, log security event
- Duplicate event → Return 200 immediately, skip processing
- Queue full → Return 503, GitHub will retry

**Performance Considerations:**
- Response time <100ms (GitHub times out at 10s)
- Async validation and queueing
- Redis SET with TTL for deduplication (key: `webhook:{pr_id}:{commit_sha}`, TTL: 1 hour)

---

### 2. Review Orchestrator

**Responsibility:** Coordinate the entire review process

**Workflow:**
1. Fetch PR metadata from GitHub API (title, author, files changed)
2. Fetch PR diff (unified diff format)
3. Parse diff into file chunks (group by file)
4. Check repository config (`.ai-review.yml`) for custom rules
5. Query vector DB for similar past PRs
6. Invoke LangGraph multi-agent workflow
7. Collect agent outputs
8. Store review in PostgreSQL
9. Post consolidated comment to GitHub
10. Update vector DB with new patterns

**Retry Logic:**
- GitHub API failures: 3 retries with exponential backoff (1s, 2s, 4s)
- LLM API failures: 2 retries, then degrade gracefully (post partial results)
- Webhook posting failures: 5 retries, alert if all fail

**Timeout Protection:**
- Overall timeout: 5 minutes
- Per-agent timeout: 60 seconds
- If timeout exceeded: Post partial results with warning

---

### 3. GitHub Service

**Responsibility:** Abstract GitHub API interactions

**Key Methods:**
```
fetch_pull_request(repo, pr_number) → PR metadata
fetch_diff(repo, pr_number) → Unified diff string
fetch_file_contents(repo, path, ref) → File content
post_review_comment(repo, pr_number, comment) → Comment ID
create_review(repo, pr_number, event, comments) → Review ID
```

**Caching Strategy:**
- PR metadata: Cache 5 minutes (rarely changes during review)
- File contents: Cache 1 hour (immutable for given commit SHA)
- Diff: No cache (changes on every commit)

**Rate Limiting:**
- GitHub allows 5,000 req/hour
- Our budget: 3,000 req/hour (buffer for spikes)
- Track usage in Redis counter, alert at 80%

---

### 4. Diff Parser

**Responsibility:** Convert Git diff into structured format for agents

**Input:** Unified diff string
**Output:** List of changed files with hunks

**Parsing Logic:**
- Extract file paths (old vs new, handle renames)
- Parse hunks (line numbers, added/removed/context lines)
- Handle binary files (skip content, note in metadata)
- Detect file deletions vs additions vs modifications

**Optimization:**
- Focus agents on changed lines ±3 context lines
- Skip large files (>1000 lines changed) with warning
- Ignore generated files (package-lock.json, .min.js)

---

### 5. Pattern Matcher

**Responsibility:** Query vector database for similar code patterns

**Workflow:**
1. Extract code snippet from current PR
2. Generate embedding using OpenAI API
3. Query Pinecone for top 5 similar vectors (cosine similarity >0.85)
4. Filter by repository (prefer same repo patterns)
5. Return patterns with acceptance status

**Context Injection:**
- If similar pattern found with 80%+ acceptance: Boost confidence
- If similar pattern found with <40% acceptance: Lower confidence or skip
- If no similar pattern: Rely on general agent knowledge

**Performance:**
- Embedding generation: ~200ms
- Pinecone query: ~100ms
- Total overhead: ~300ms per PR (acceptable)

---

## Data Models

### Database Schema (PostgreSQL)

**repositories**
```
id: SERIAL PRIMARY KEY
github_id: BIGINT UNIQUE (GitHub's repo ID)
name: VARCHAR(255) (e.g., "ai-code-reviewer")
full_name: VARCHAR(512) (e.g., "vivek/ai-code-reviewer")
owner: VARCHAR(255)
config: JSONB (parsed .ai-review.yml)
is_active: BOOLEAN
created_at: TIMESTAMP
updated_at: TIMESTAMP

Indexes:
- github_id (unique)
- full_name (for lookups)
```

**pull_requests**
```
id: SERIAL PRIMARY KEY
github_id: BIGINT UNIQUE
repository_id: INTEGER (FK → repositories)
number: INTEGER (PR #123)
title: VARCHAR(512)
author: VARCHAR(255)
state: VARCHAR(50) (open, closed, merged)
base_branch: VARCHAR(255)
head_branch: VARCHAR(255)
diff_url: TEXT
files_changed: INTEGER
additions: INTEGER
deletions: INTEGER
created_at: TIMESTAMP
updated_at: TIMESTAMP

Indexes:
- github_id (unique)
- repository_id, number (composite for fast lookups)
- state (for filtering)
```

**reviews**
```
id: SERIAL PRIMARY KEY
pull_request_id: INTEGER (FK → pull_requests)
status: VARCHAR(50) (pending, completed, failed, partial)
total_issues: INTEGER
critical_issues: INTEGER
warnings: INTEGER
suggestions: INTEGER
processing_time_ms: INTEGER
cost_usd: DECIMAL(10,4) (API costs)
agent_versions: JSONB (which agent versions ran)
created_at: TIMESTAMP
completed_at: TIMESTAMP

Indexes:
- pull_request_id
- status
- created_at (for time-series queries)
```

**comments**
```
id: SERIAL PRIMARY KEY
review_id: INTEGER (FK → reviews)
github_comment_id: BIGINT (GitHub's comment ID)
file_path: VARCHAR(1024)
line_number: INTEGER
agent_type: VARCHAR(50) (style, security, performance, bug)
severity: VARCHAR(20) (critical, warning, suggestion)
message: TEXT
code_snippet: TEXT (problematic code)
suggestion: TEXT (recommended fix)
accepted: BOOLEAN (did dev implement suggestion?)
confidence_score: DECIMAL(3,2) (0.00-1.00)
created_at: TIMESTAMP

Indexes:
- review_id
- agent_type, severity (for analytics)
- accepted (for learning system)
```

**patterns**
```
id: SERIAL PRIMARY KEY
repository_id: INTEGER (FK → repositories)
pattern_type: VARCHAR(50) (style, security, etc.)
description: TEXT
example_code: TEXT
vector_id: VARCHAR(255) (Pinecone ID)
positive_votes: INTEGER (accepted count)
negative_votes: INTEGER (rejected count)
language: VARCHAR(50) (python, javascript, etc.)
created_at: TIMESTAMP

Indexes:
- repository_id
- pattern_type
- language
- vector_id (for Pinecone sync)
```

### Vector Database Schema (Pinecone)

**Index Configuration:**
```
Name: code-review-patterns
Dimension: 1536 (OpenAI embedding size)
Metric: cosine
```

**Vector Metadata:**
```
{
  "pattern_id": 123,              // PostgreSQL patterns.id
  "repository_id": 5,
  "pattern_type": "style",
  "language": "python",
  "accepted": true,
  "votes": 15,                    // positive_votes - negative_votes
  "confidence": 0.92,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Query Strategy:**
```
top_k = 5
filter = {
  "repository_id": current_repo_id,  // Prefer same repo
  "language": detected_language
}
min_similarity = 0.85
```

---

## API Design

### REST Endpoints

**Webhook Endpoint**
```
POST /api/webhooks/github
Headers:
  X-GitHub-Event: pull_request
  X-Hub-Signature-256: sha256=...
Body: GitHub webhook payload
Response: 200 OK (always, even if queued)
```

**Review Status**
```
GET /api/reviews/{review_id}
Response:
{
  "id": 123,
  "status": "completed",
  "total_issues": 12,
  "critical_issues": 2,
  "warnings": 5,
  "suggestions": 5,
  "processing_time_ms": 45000,
  "cost_usd": 0.12,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**PR Reviews List**
```
GET /api/pull-requests/{pr_id}/reviews
Query Params:
  ?status=completed&limit=10
Response:
{
  "reviews": [...],
  "pagination": {
    "total": 25,
    "page": 1,
    "per_page": 10
  }
}
```

**Analytics**
```
GET /api/analytics/repository/{repo_id}/summary
Query Params:
  ?start_date=2024-01-01&end_date=2024-01-31
Response:
{
  "total_reviews": 150,
  "avg_processing_time_ms": 42000,
  "acceptance_rate": 0.82,
  "cost_total_usd": 18.50,
  "issues_by_severity": {
    "critical": 45,
    "warning": 120,
    "suggestion": 280
  },
  "top_issue_types": [
    {"type": "security.sql_injection", "count": 12},
    {"type": "style.naming_convention", "count": 35}
  ]
}
```

### Internal Service APIs

**GitHub Service Interface**
```
GitHubService:
  - fetch_pr(repo: str, pr_number: int) → PullRequest
  - fetch_diff(repo: str, pr_number: int) → str
  - post_comment(repo: str, pr_number: int, body: str) → Comment
  - update_review_status(repo: str, pr_number: int, status: str)
```

**Pattern Matcher Interface**
```
PatternMatcher:
  - find_similar_patterns(code: str, language: str, repo_id: int) → List[Pattern]
  - store_pattern(code: str, metadata: dict) → str (vector_id)
  - update_pattern_vote(pattern_id: int, accepted: bool)
```

**Review Orchestrator Interface**
```
ReviewOrchestrator:
  - process_pr(pr_id: int) → Review
  - retry_failed_review(review_id: int)
  - get_review_status(review_id: int) → dict
```

---

## Multi-Agent System

### Agent Architecture

**Base Agent Interface:**
```
BaseAgent:
  - analyze(code: str, context: dict) → List[Issue]
  - confidence() → float (0.0-1.0)
  - agent_type() → str
```

### Agent Specializations

**1. Style Agent**
- **Focus:** Code formatting, naming conventions, structure
- **Checks:**
  - Naming conventions (camelCase vs snake_case)
  - Function length (>50 lines flagged)
  - Cyclomatic complexity (>10 flagged)
  - Import organization
  - Docstring presence
- **Prompt Strategy:**
  - Include team's style guide from vector DB
  - Compare against PEP 8 (Python) or Airbnb style (JS)
  - Conservative: Only flag clear violations

**2. Security Agent**
- **Focus:** Security vulnerabilities
- **Checks:**
  - SQL injection risks (string concatenation in queries)
  - XSS vulnerabilities (unescaped user input)
  - Hardcoded secrets (API keys, passwords in code)
  - Insecure dependencies (known CVEs)
  - Authentication bypasses
  - CSRF vulnerabilities
- **Prompt Strategy:**
  - Use OWASP Top 10 as reference
  - Request code-flow analysis for input handling
  - High severity only for confirmed vulnerabilities

**3. Performance Agent**
- **Focus:** Algorithmic efficiency, resource usage
- **Checks:**
  - O(n²) loops (nested iterations)
  - N+1 query problems (ORMs)
  - Memory leaks (unclosed resources)
  - Blocking operations in async code
  - Inefficient data structures (list vs set for lookups)
- **Prompt Strategy:**
  - Analyze algorithmic complexity
  - Consider data volume context
  - Suggest optimizations with examples

**4. Bug Detector Agent**
- **Focus:** Logic errors, edge cases, type issues
- **Checks:**
  - Null/undefined access risks
  - Off-by-one errors
  - Race conditions
  - Exception handling gaps
  - Type mismatches (if TypeScript/typed Python)
- **Prompt Strategy:**
  - Trace execution paths
  - Consider edge cases (empty arrays, null values)
  - Check error propagation

**5. Synthesizer Agent**
- **Focus:** Combine all findings, remove duplicates, prioritize
- **Logic:**
  - Deduplicate similar issues from different agents
  - Rank by severity × confidence
  - Format into single coherent review
  - Add summary statistics
- **Output Format:**
  ```
  ## Code Review Summary
  
  **Overall:** 12 issues found (2 critical, 5 warnings, 5 suggestions)
  **Processing time:** 45 seconds
  
  ### Critical Issues
  1. [Security] SQL Injection risk in user_query.py:45
     - Current: `db.execute(f"SELECT * FROM users WHERE id={user_id}")`
     - Fix: Use parameterized query
  
  ### Warnings
  ...
  ```

### LangGraph Workflow

**Graph Structure:**
```
START
  ↓
Parse PR Diff
  ↓
Query Vector DB (parallel)
  ↓
┌─────────┬─────────┬─────────┬─────────┐
│ Style   │Security │Performance│  Bug   │
│ Agent   │ Agent   │  Agent   │ Agent  │
└────┬────┴────┬────┴────┬─────┴────┬────┘
     │         │         │          │
     └─────────┼─────────┼──────────┘
               ↓
         Synthesizer
               ↓
         Store Results
               ↓
         Post to GitHub
               ↓
              END
```

**State Management:**
```
ReviewState:
  - pr_data: PullRequest
  - diff: ParsedDiff
  - similar_patterns: List[Pattern]
  - style_issues: List[Issue]
  - security_issues: List[Issue]
  - performance_issues: List[Issue]
  - bug_issues: List[Issue]
  - final_review: Review
```

**Conditional Routing:**
- If PR has >100 files: Skip performance agent (too slow)
- If no Python/JS files: Skip style agent
- If security agent finds critical issue: Escalate immediately

---

## Learning System

### Feedback Detection

**Positive Signals (Suggestion Accepted):**
- Developer commits code matching suggestion within 24 hours
- Exact pattern match: 100% confidence
- Fuzzy match: 70% confidence (same intent, different implementation)

**Negative Signals (Suggestion Rejected):**
- Developer dismisses agent comment
- Code remains unchanged after 7 days
- Developer argues against suggestion in comment

**Implementation:**
```
CompareEngine:
  - compare_code_before_after(old: str, new: str, suggestion: str) → float (similarity score)
  - Uses AST comparison for structural similarity
  - Ignores whitespace/formatting differences
```

### Embedding Generation

**What Gets Embedded:**
- Code snippet (problematic code)
- Suggestion text
- File path and language
- Issue type (style.naming, security.sql_injection)

**Embedding Process:**
1. Construct context string:
   ```
   Language: Python
   File: user_service.py
   Issue: security.sql_injection
   Code: db.execute(f"SELECT * FROM users WHERE id={user_id}")
   Suggestion: Use parameterized queries to prevent SQL injection
   ```
2. Call OpenAI Embedding API
3. Receive 1536-dim vector
4. Store in Pinecone with metadata

### Pattern Matching at Review Time

**Query Construction:**
```
QueryBuilder:
  - Extract code snippet from current PR
  - Detect language (from file extension)
  - Generate embedding
  - Build Pinecone filter (repository_id, language)
  - Query top_k=5, min_score=0.85
```

**Confidence Adjustment:**
```
if similar_patterns found:
  acceptance_rate = positive_votes / (positive_votes + negative_votes)
  
  if acceptance_rate > 0.8:
    confidence *= 1.2  // Boost confidence
  elif acceptance_rate < 0.4:
    confidence *= 0.5  // Lower confidence
  
  Add context to review:
    "This team typically accepts this pattern (4/5 past cases)"
```

### Continuous Improvement

**Weekly Analysis:**
- Calculate acceptance rate per agent
- Identify frequently rejected issue types
- Adjust prompts or disable low-value checks

**Monthly Review:**
- Analyze false positives/negatives
- Update base prompts
- Retrain pattern matching thresholds

---

## Performance & Scalability

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Webhook response time | <100ms | TBD |
| Review completion (small PR <10 files) | <30s | TBD |
| Review completion (medium PR 10-50 files) | <60s | TBD |
| Review completion (large PR 50-100 files) | <120s | TBD |
| Concurrent PR reviews | 10 | TBD |
| System uptime | 99.5% | TBD |

### Scalability Strategy

**Horizontal Scaling:**
- FastAPI instances: Scale behind load balancer (Nginx)
- Celery workers: Add more workers for increased throughput
- PostgreSQL: Read replicas for analytics queries
- Redis: Redis Cluster for >10GB data

**Vertical Scaling:**
- Current: 2GB RAM, 2 vCPU per worker
- Max: 8GB RAM, 4 vCPU before horizontal scaling

**Bottleneck Analysis:**
1. **LLM API calls:** Slowest step (2-5s per agent)
   - Mitigation: Parallel execution, caching
2. **GitHub API:** Rate limited
   - Mitigation: Caching, batching
3. **Database writes:** Minimal impact
   - Mitigation: Async writes, batching

### Caching Strategy

**Redis Cache Keys:**
```
pr:{repo}:{pr_number}:metadata    TTL: 5 minutes
pr:{repo}:{pr_number}:diff        TTL: 1 hour (immutable per commit)
file:{repo}:{sha}:{path}          TTL: 24 hours (immutable)
pattern:{code_hash}:embedding     TTL: 7 days
github:rate_limit:remaining       TTL: 1 hour
```

**Cache Hit Ratio Target:** >70%

### Cost Optimization

**API Cost Breakdown (per PR):**
```
Claude API (4 agents × 2K tokens avg):
  Input: 8K tokens × $3/M = $0.024
  Output: 2K tokens × $15/M = $0.030
  Total: $0.054 per PR

OpenAI Embeddings (2 patterns avg):
  2 × 500 tokens × $0.02/M = $0.00002
  
Pinecone queries:
  Free tier: 100/day, sufficient for MVP

Total cost: ~$0.054 per PR
Monthly (500 PRs): ~$27
```

**Optimization Tactics:**
1. Cache identical code snippets (20% reduction)
2. Skip unchanged files on PR updates (30% reduction)
3. Progressive review (review only new commits)
4. Batch embeddings (5 at a time)

**Target:** <$50/month for 500 PRs

---

## Security

### Authentication & Authorization

**GitHub App Authentication:**
- Private key stored in environment variable (never in code)
- JWT generation for API calls (expires 10 minutes)
- Installation access token (expires 1 hour, cached)

**Webhook Validation:**
```
HMAC-SHA256(payload, webhook_secret) == X-Hub-Signature-256
If match: Process
Else: Reject with 401, log security event
```

**API Security:**
- No public endpoints (except webhooks)
- Future: API key authentication for dashboard
- Rate limiting: 100 req/min per IP

### Data Privacy

**PII Handling:**
- Store: PR number, repo name, timestamps
- DO NOT store: Developer emails, full names, commit messages
- GitHub usernames: Stored for attribution, anonymized in analytics

**Code Privacy:**
- Full diffs: Never persisted to disk or database
- Code snippets: Stored in comments table, encrypted at rest
- Review comments: Public on GitHub, stored for learning (opt-out available)

**Compliance:**
- GDPR: Right to deletion implemented via `/api/privacy/delete-user-data`
- Data retention: Reviews stored 1 year, then archived
- Audit logs: All data access logged, retained 90 days

### Secrets Management

**Environment Variables:**
```
GITHUB_PRIVATE_KEY_PATH=/secrets/github-app-key.pem
ANTHROPIC_API_KEY=sk-ant-***
OPENAI_API_KEY=sk-***
PINECONE_API_KEY=***
DATABASE_URL=postgresql://***
WEBHOOK_SECRET=***
```

**Never in Code:**
- API keys hardcoded
- Connection strings
- Encryption keys

**Secret Rotation:**
- GitHub app key: Yearly
- API keys: On compromise or quarterly
- Webhook secret: On compromise

### Threat Model

**Threat 1: Malicious Webhook Payload**
- Mitigation: HMAC validation, Pydantic schema validation
- Impact: Low (rejected before processing)

**Threat 2: Prompt Injection via PR Content**
- Scenario: Attacker crafts PR with malicious prompt in code comments
- Mitigation: Strict prompt templates, output validation
- Impact: Medium (could bias review, but doesn't expose data)

**Threat 3: API Key Exposure**
- Mitigation: Environment variables, never log keys, rotation policy
- Impact: High (unauthorized API usage)

**Threat 4: Database Compromise**
- Mitigation: Encryption at rest, least-privilege access, VPC isolation
- Impact: High (review history leaked)

**Threat 5: DDoS on Webhook Endpoint**
- Mitigation: Rate limiting, GitHub IP whitelist, queue buffering
- Impact: Medium (delays reviews, doesn't expose data)

---

## Deployment

### Infrastructure Requirements

**Production Environment:**
```
- 1 FastAPI instance: 2GB RAM, 2 vCPU
- 2 Celery workers: 2GB RAM each, 2 vCPU
- 1 PostgreSQL: 4GB RAM, 2 vCPU, 20GB SSD
- 1 Redis: 1GB RAM, 1 vCPU
- Total: ~$50-80/month (DigitalOcean, Railway, Render)
```

**Development Environment:**
```
- Docker Compose on local machine
- PostgreSQL, Redis, App, Worker containers
- Ngrok for webhook testing
```

### Deployment Strategy

**CI/CD Pipeline (GitHub Actions):**
```
On PR:
  - Run linter (ruff)
  - Run type checker (mypy)
  - Run tests (pytest)
  - Build Docker image
  - Deploy to staging (if main branch)

On Merge to Main:
  - Run full test suite
  - Build production Docker image
  - Push to Docker Hub
  - Deploy to production (Railway auto-deploy)
  - Run smoke tests
  - Notify Slack channel
```

**Zero-Downtime Deployment:**
- Blue-green deployment
- Health check endpoint: `/health`
- Load balancer switches after health check passes

**Rollback Strategy:**
- Keep last 3 Docker images
- Rollback via Railway dashboard or CLI
- Database migrations reversible (Alembic downgrade)

### Environment Configuration

**Development:**
```
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost:5432/dev_db
ANTHROPIC_API_KEY=test-key (use free tier)
```

**Staging:**
```
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://staging-db:5432/staging
ANTHROPIC_API_KEY=staging-key
```

**Production:**
```
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod-db:5432/prod
ANTHROPIC_API_KEY=prod-key
SENTRY_DSN=https://... (error tracking)
```

---

## Monitoring & Observability

### Logging Strategy

**Structured Logging (JSON):**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "review-orchestrator",
  "trace_id": "abc123",
  "message": "Review completed",
  "pr_id": 456,
  "processing_time_ms": 45000,
  "cost_usd": 0.12
}
```

**Log Levels:**
- DEBUG: Detailed flow (dev only)
- INFO: Key events (review started, completed)
- WARNING: Recoverable errors (API retry, timeout)
- ERROR: Failures requiring attention
- CRITICAL: System-wide issues (DB down, API keys invalid)

**Log Aggregation:**
- Tool: Papertrail (free tier) or Grafana Loki
- Retention: 7 days (development), 30 days (production)
- Searchable by: trace_id, pr_id, error_type

### Metrics Collection

**Key Metrics (Prometheus format):**
```
review_duration_seconds{status="completed"} → Histogram
review_cost_usd{agent="style"} → Counter
webhook_events_total{event_type="pull_request"} → Counter
api_calls_total{service="github", status="200"} → Counter
cache_hit_ratio{cache_type="pr_metadata"} → Gauge
queue_depth{queue="celery"} → Gauge
```

**Dashboards (Grafana):**
1. **System Health:**
   - Request rate, error rate, latency (RED metrics)
   - Queue depth, worker utilization
   - Database connections, CPU/memory

2. **Business Metrics:**
   - Reviews per day/week
   - Acceptance rate trend
   - Cost per review
   - Issue distribution (critical/warning/suggestion)

3. **Agent Performance:**
   - Per-agent latency
   - Per-agent accuracy (based on acceptance)
   - False positive rate

### Alerting Rules

**Critical Alerts (PagerDuty/Slack):**
- Error rate >5% for 5 minutes → Page on-call
- Database connection failures → Immediate alert
- Daily cost >$10 → Alert team lead
- Review queue >50 for 10 minutes → Alert (backlog forming)

**Warning Alerts (Slack only):**
- Review latency P95 >90s
- Cache hit ratio <60%
- Webhook signature validation failures >10/hour

**Health Checks:**
```
GET /health
Response:
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok",
    "github_api": "ok"
  },
  "version": "1.0.0",
  "uptime_seconds": 86400
}
```

### Error Tracking

**Sentry Integration:**
- Automatic error capture with stack traces
- Breadcrumbs: Recent log entries before error
- User context: PR ID, repository
- Release tracking: Tag errors by deployment version

**Error Budget:**
- Target: 99.5% success rate (500 errors per 100K requests)
- Monthly review: If budget exhausted, prioritize stability over features

---

## Technology Decision Log

### Why FastAPI over Flask/Django?

**Context:** Need async webhook handling, auto API docs, modern Python

**Options:**
1. Flask: Simple, mature, but no native async
2. Django: Batteries included, but heavy for API-only service
3. FastAPI: Async-first, OpenAPI docs, Pydantic validation

**Decision:** FastAPI
- Native async critical for webhook concurrency
- OpenAPI docs save documentation effort
- Pydantic models reduce boilerplate validation

**Trade-offs:**
- Smaller community than Flask/Django
- Fewer plugins available
- Accepted: Community growing fast, async worth it

---

### Why Claude over GPT-4 for Code Review?

**Context:** Need LLM for code analysis

**Options:**
1. GPT-4: General purpose, widely used
2. Claude: Better at reasoning, longer context
3. Gemini: Multimodal, good code understanding

**Decision:** Claude Sonnet 4.5
- 200K context (entire PR in one call)
- Superior code reasoning vs GPT-4
- Structured outputs (JSON mode)

**Trade-offs:**
- Costs 20% more than GPT-4
- Smaller ecosystem
- Accepted: Code quality worth extra cost

---

### Why Celery over FastAPI BackgroundTasks?

**Context:** Need async processing for PR reviews

**Options:**
1. FastAPI BackgroundTasks: Built-in, simple
2. Celery: Feature-rich, battle-tested
3. RQ (Redis Queue): Simpler than Celery

**Decision:** Celery
- Retry logic, priority queues, periodic tasks
- Monitoring tools (Flower)
- Production-proven at scale

**Trade-offs:**
- More complex setup than BackgroundTasks
- Requires Redis/RabbitMQ
- Accepted: Need reliability for production

---

### Why Pinecone over Weaviate?

**Context:** Need vector database for pattern learning

**Options:**
1. Pinecone: Managed, simple API
2. Weaviate: Self-hosted, more control
3. PostgreSQL pgvector: Integrated with main DB

**Decision:** Pinecone
- 1M vectors free (sufficient for MVP)
- Zero ops overhead
- Simple API, fast queries

**Trade-offs:**
- Vendor lock-in
- Limited free tier
- Accepted: Simplicity > control for MVP, can migrate later

---

## Appendix

### Glossary

- **Agent:** Specialized AI component analyzing one review aspect
- **Embedding:** Vector representation of code for similarity search
- **Webhook:** HTTP callback from GitHub when PR events occur
- **Diff:** Git's representation of file changes
- **Hunk:** Section of a diff showing specific line changes
- **Review:** Complete analysis output from all agents
- **Pattern:** Learned code snippet with acceptance history

### References

- [GitHub Webhook Events](https://docs.github.com/en/webhooks/webhook-events-and-payloads)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Pinecone Vector Database](https://docs.pinecone.io/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)

---

**Document Status:** ✅ Ready for Implementation  
**Next Review:** End of Week 1  
**Change Log:** v1.0 - Initial Technical Spec (Jan 2025)
