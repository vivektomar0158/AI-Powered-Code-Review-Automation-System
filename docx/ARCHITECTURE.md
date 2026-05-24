# System Architecture
## AI Code Review Agent

**Version:** 1.0  
**Author:** Vivek  
**Date:** January 2025  
**Status:** Design Phase

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Multi-Agent Architecture](#multi-agent-architecture)
5. [Integration Patterns](#integration-patterns)
6. [Scalability Design](#scalability-design)
7. [Security Architecture](#security-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Technology Decisions](#technology-decisions)

---

## Architecture Overview

### System Type

**Event-Driven Microservices Architecture** with asynchronous processing and multi-agent AI orchestration.

### Core Architectural Patterns

1. **Event-Driven:** GitHub webhooks trigger processing pipelines
2. **Producer-Consumer:** Celery workers consume review jobs from Redis queue
3. **Multi-Agent System:** Specialized AI agents collaborate via LangGraph
4. **CQRS (Light):** Separate read/write paths for analytics
5. **Repository Pattern:** Data access abstraction layer
6. **Strategy Pattern:** Configurable agent selection and routing

### Key Design Goals

| Goal | Implementation | Benefit |
|------|----------------|---------|
| **Fast Response** | Async webhook processing, parallel agents | <60s review time |
| **Cost Efficiency** | Caching, incremental reviews | <$50/month for 500 PRs |
| **Reliability** | Retry logic, partial results, monitoring | 99.5% uptime |
| **Extensibility** | Plugin architecture for new agents | Easy to add features |
| **Learning** | Feedback loop with vector storage | Improves over time |

---

## System Components

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          External Services                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │   GitHub     │   │  Anthropic   │   │   OpenAI     │          │
│  │     API      │   │   Claude     │   │  Embeddings  │          │
│  │  (Webhooks)  │   │     API      │   │     API      │          │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘          │
│         │                  │                  │                    │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
          │ HTTPS            │ HTTPS            │ HTTPS
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────────┐
│                      Application Layer                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Web Server                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐            │  │
│  │  │  Webhook   │  │   Review   │  │ Analytics  │            │  │
│  │  │  Handler   │  │   API      │  │    API     │            │  │
│  │  └─────┬──────┘  └────────────┘  └────────────┘            │  │
│  └────────┼─────────────────────────────────────────────────────┘  │
│           │ Enqueue job                                             │
│           ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 Background Workers (Celery)                   │  │
│  │                                                                │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │           Review Orchestrator Service                   │ │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │ │  │
│  │  │  │   GitHub     │  │     Diff     │  │   Pattern    │  │ │  │
│  │  │  │   Service    │  │    Parser    │  │   Matcher    │  │ │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘  │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  │                           │                                   │  │
│  │                           ▼                                   │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │            LangGraph Agent Orchestration                │ │  │
│  │  │                                                          │ │  │
│  │  │    ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐             │ │  │
│  │  │    │Style │  │Security│ │Perf  │  │ Bug  │             │ │  │
│  │  │    │Agent │  │ Agent  │ │Agent │  │Agent │             │ │  │
│  │  │    └───┬──┘  └───┬───┘  └───┬──┘  └───┬──┘             │ │  │
│  │  │        │         │          │         │                 │ │  │
│  │  │        └─────────┼──────────┼─────────┘                 │ │  │
│  │  │                  ▼          │                            │ │  │
│  │  │           ┌────────────┐    │                            │ │  │
│  │  │           │Synthesizer │◄───┘                            │ │  │
│  │  │           └────────────┘                                 │ │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │ PostgreSQL   │   │    Redis     │   │   Pinecone   │          │
│  │              │   │              │   │    Vector    │          │
│  │ - Repos      │   │ - Queue      │   │      DB      │          │
│  │ - PRs        │   │ - Cache      │   │              │          │
│  │ - Reviews    │   │ - Dedup      │   │ - Patterns   │          │
│  │ - Comments   │   │ - Locks      │   │ - Embeddings │          │
│  │ - Patterns   │   │              │   │              │          │
│  └──────────────┘   └──────────────┘   └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Component Descriptions

#### 1. FastAPI Web Server

**Purpose:** HTTP request handling, webhook validation, API endpoints

**Responsibilities:**
- Receive GitHub webhooks
- Validate HMAC signatures
- Serve REST API for reviews, analytics
- Health check endpoints
- OpenAPI documentation

**Technology:** FastAPI 0.110+, Uvicorn ASGI server

**Scaling:** Horizontal - add more instances behind load balancer

---

#### 2. Celery Background Workers

**Purpose:** Asynchronous processing of review jobs

**Responsibilities:**
- Pick jobs from Redis queue
- Execute review orchestration
- Retry failed jobs with exponential backoff
- Report progress and results

**Technology:** Celery 5.3+ with Redis broker

**Scaling:** Horizontal - increase worker count based on queue depth

**Worker Configuration:**
```python
# celery_config.py
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'

task_routes = {
    'review.process_pr': {'queue': 'reviews'},
    'analytics.compute': {'queue': 'analytics'}
}

task_annotations = {
    'review.process_pr': {
        'rate_limit': '10/m',  # 10 reviews per minute max
        'time_limit': 300,      # 5 minute timeout
        'soft_time_limit': 240  # Soft timeout at 4 minutes
    }
}
```

---

#### 3. Review Orchestrator

**Purpose:** Coordinate the end-to-end review process

**Workflow:**
1. Fetch PR data from GitHub
2. Parse diff into structured format
3. Load repository configuration
4. Query pattern matcher for similar past cases
5. Build LangGraph state with context
6. Execute multi-agent workflow
7. Collect and synthesize results
8. Store review in database
9. Post comment to GitHub
10. Update learning patterns

**Key Services Used:**
- GitHub Service (API client)
- Diff Parser (parse Git diffs)
- Pattern Matcher (vector search)
- LangGraph Executor

---

#### 4. GitHub Service

**Purpose:** Abstract all GitHub API interactions

**Key Methods:**
```python
class GitHubService:
    async def fetch_pull_request(repo: str, pr_number: int) -> PullRequest
    async def fetch_diff(repo: str, pr_number: int) -> str
    async def fetch_file_contents(repo: str, path: str, ref: str) -> str
    async def post_review_comment(repo: str, pr: int, body: str) -> Comment
    async def create_review(repo: str, pr: int, event: str, comments: List) -> Review
```

**Features:**
- Automatic token refresh (JWT → installation token)
- Rate limit tracking and backoff
- Response caching (Redis)
- Retry with exponential backoff

**GitHub App Authentication Flow:**
```
1. Generate JWT from private key (expires 10 min)
2. Exchange JWT for installation access token (expires 1 hour)
3. Cache token in Redis with 50 min TTL
4. Use token for API calls
5. Refresh when expired
```

---

#### 5. Diff Parser

**Purpose:** Convert Git unified diff into structured data

**Input:**
```diff
diff --git a/src/auth.py b/src/auth.py
index abc123..def456 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,7 +10,8 @@ def login(username, password):
-    query = f"SELECT * FROM users WHERE name='{username}'"
+    query = "SELECT * FROM users WHERE name=%s"
+    cursor.execute(query, (username,))
```

**Output:**
```python
ParsedDiff(
    files=[
        FileChange(
            path="src/auth.py",
            old_path="src/auth.py",
            status="modified",
            hunks=[
                Hunk(
                    old_start=10,
                    old_lines=7,
                    new_start=10,
                    new_lines=8,
                    changes=[
                        Change(type="removed", line_num=10, 
                               content='query = f"SELECT * FROM users WHERE name=\'{username}\'"'),
                        Change(type="added", line_num=10, 
                               content='query = "SELECT * FROM users WHERE name=%s"'),
                        Change(type="added", line_num=11, 
                               content='cursor.execute(query, (username,))')
                    ]
                )
            ]
        )
    ]
)
```

**Features:**
- Handles renames, deletions, binary files
- Preserves context lines (±3 around changes)
- Filters generated files (.min.js, package-lock.json)

---

#### 6. Pattern Matcher

**Purpose:** Find similar code patterns from past reviews

**Process:**
```
Code Snippet → OpenAI Embedding API → 1536D Vector
                    ↓
              Pinecone Query
         (cosine similarity > 0.85)
                    ↓
           Top 5 Similar Patterns
                    ↓
         Filter by Repository & Language
                    ↓
      Return with Acceptance Rates
```

**Query Optimization:**
- Batch embeddings (5 at a time) to reduce API calls
- Cache embeddings for identical code snippets (Redis, 7 day TTL)
- Pinecone metadata filtering reduces search space

**Example:**
```python
# Find similar patterns
patterns = await pattern_matcher.find_similar(
    code="query = f\"SELECT * FROM users WHERE id={user_id}\"",
    language="python",
    repo_id=123,
    top_k=5
)

# Returns:
[
    Pattern(
        id=456,
        description="SQL injection via f-string",
        acceptance_rate=0.95,
        positive_votes=19,
        similarity=0.92
    ),
    ...
]
```

---

#### 7. LangGraph Multi-Agent System

**Purpose:** Orchestrate multiple specialized AI agents in a workflow

**Graph Structure:**
```
        START
          │
          ▼
    ┌──────────┐
    │  Parse   │
    │   Diff   │
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │  Query   │
    │ Patterns │
    └────┬─────┘
         │
         ▼
    ┌────────────────────────┐
    │  Parallel Agent Exec   │
    ├────────────────────────┤
    │  ┌────┐  ┌────┐       │
    │  │ S  │  │ Se │       │
    │  │ ty │  │ cu │       │
    │  │ le │  │ ri │       │
    │  └─┬──┘  └─┬──┘       │
    │    │       │          │
    │  ┌─▼───┐ ┌▼───┐      │
    │  │Perf │ │Bug │      │
    │  └──┬──┘ └─┬──┘      │
    │     │      │          │
    └─────┼──────┼──────────┘
          │      │
          ▼      ▼
    ┌──────────────┐
    │ Synthesizer  │
    │  - Dedupe    │
    │  - Prioritize│
    │  - Format    │
    └──────┬───────┘
           │
           ▼
    ┌──────────┐
    │  Store   │
    │ Results  │
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │   Post   │
    │ to GitHub│
    └────┬─────┘
         │
         ▼
        END
```

**State Object:**
```python
@dataclass
class ReviewState:
    pr_data: PullRequest
    diff: ParsedDiff
    similar_patterns: List[Pattern]
    repo_config: Config
    
    # Agent outputs
    style_issues: List[Issue] = field(default_factory=list)
    security_issues: List[Issue] = field(default_factory=list)
    performance_issues: List[Issue] = field(default_factory=list)
    bug_issues: List[Issue] = field(default_factory=list)
    
    # Final output
    synthesized_review: Review = None
```

**Conditional Logic:**
```python
def route_to_agents(state: ReviewState) -> List[str]:
    """Decide which agents to run based on PR characteristics"""
    agents = ["style", "security"]  # Always run these
    
    if state.pr_data.files_changed < 100:
        agents.append("performance")  # Skip for large PRs (too slow)
    
    if any(f.path.endswith(('.py', '.js', '.java')) 
           for f in state.diff.files):
        agents.append("bug")  # Only for code files
    
    return agents
```

---

## Data Flow

### Primary Flow: PR Created → Review Posted

```
┌──────────┐
│ Developer│
│ Creates  │
│   PR     │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────────┐
│           GitHub Platform               │
│  ┌────────────────────────────────┐    │
│  │  Fires "pull_request.opened"   │    │
│  │        Webhook Event            │    │
│  └──────────────┬──────────────────┘    │
└─────────────────┼───────────────────────┘
                  │
                  │ POST /api/webhooks/github
                  │ X-Hub-Signature-256: sha256=...
                  │
                  ▼
┌──────────────────────────────────────────┐
│      FastAPI Webhook Endpoint            │
│                                          │
│  1. Verify HMAC signature               │
│  2. Parse payload                       │
│  3. Check Redis dedup cache             │
│  4. Enqueue to Celery                   │
│                                          │
│  Response: 200 OK (45s estimate)        │
└──────────────┬────────────────────────────┘
               │
               │ Job: review_pr(pr_id=123)
               │
               ▼
┌──────────────────────────────────────────┐
│         Redis Queue (Celery)             │
│                                          │
│  Key: celery:task:abc-123-def           │
│  Value: {task: review_pr, args: [123]}  │
│  TTL: 1 hour                             │
└──────────────┬────────────────────────────┘
               │
               │ Worker picks job
               │
               ▼
┌──────────────────────────────────────────┐
│      Celery Worker Process               │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   Review Orchestrator Start        │ │
│  │   - Update status: "processing"    │ │
│  │   - Set timeout: 5 minutes         │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────────┐ │
│  │   Fetch PR from GitHub API         │ │
│  │   GET /repos/{owner}/{repo}/pulls  │ │
│  │   Cache: 5 min                     │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────────┐ │
│  │   Fetch Diff                       │ │
│  │   GET {pr.diff_url}                │ │
│  │   Parse into structured format     │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────────┐ │
│  │   Query Pattern Matcher            │ │
│  │   - Generate embeddings (OpenAI)   │ │
│  │   - Search Pinecone (top 5)        │ │
│  │   - Filter by repo & language      │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────────┐ │
│  │   Execute LangGraph Workflow       │ │
│  │                                    │ │
│  │   Parallel Execution:              │ │
│  │   ┌─────────┐ ┌─────────┐         │ │
│  │   │ Style   │ │Security │         │ │
│  │   │ Agent   │ │ Agent   │         │ │
│  │   │ (3s)    │ │ (4s)    │         │ │
│  │   └────┬────┘ └────┬────┘         │ │
│  │        │           │              │ │
│  │   ┌────▼────┐ ┌───▼─────┐        │ │
│  │   │  Perf   │ │   Bug   │        │ │
│  │   │ Agent   │ │  Agent  │        │ │
│  │   │ (5s)    │ │  (3s)   │        │ │
│  │   └────┬────┘ └────┬────┘        │ │
│  │        │           │              │ │
│  │        └─────┬─────┘              │ │
│  │              ▼                    │ │
│  │      ┌──────────────┐            │ │
│  │      │ Synthesizer  │            │ │
│  │      │  (2s)        │            │ │
│  │      └──────┬───────┘            │ │
│  │             │                    │ │
│  │   Total: ~15s (parallel)         │ │
│  └─────────────┬────────────────────┘ │
│                │                       │
│                ▼                       │
│  ┌────────────────────────────────────┐ │
│  │   Store Results in PostgreSQL      │ │
│  │   - Review record                  │ │
│  │   - 12 comment records             │ │
│  │   - Processing time: 45230ms       │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────────┐ │
│  │   Post Review to GitHub            │ │
│  │   POST /repos/.../pulls/42/reviews │ │
│  │   Body: Formatted review comment   │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────────┐ │
│  │   Update Patterns (Async)          │ │
│  │   - Generate embeddings            │ │
│  │   - Store in Pinecone              │ │
│  │   - Link to PostgreSQL             │ │
│  └────────────┬───────────────────────┘ │
│               │                          │
│               ▼                          │
│  ┌────────────────────────────────────┐ │
│  │   Mark Status: "completed"         │ │
│  │   Total time: 45 seconds           │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
                  │
                  │ Notification
                  │
                  ▼
┌──────────────────────────────────────────┐
│           GitHub Platform               │
│  ┌────────────────────────────────┐    │
│  │  Review comment appears on PR  │    │
│  │  Developer receives notification│    │
│  └────────────────────────────────┘    │
└──────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│          Developer Reviews               │
│  - Reads agent suggestions              │
│  - Fixes critical issues                │
│  - Pushes new commit                    │
│  - Triggers new review (incremental)    │
└──────────────────────────────────────────┘
```

### Timing Breakdown

| Stage | Time | Cumulative |
|-------|------|------------|
| Webhook received → Queued | <100ms | 0.1s |
| Worker picks job | <1s | 1.1s |
| Fetch PR metadata (cached) | 200ms | 1.3s |
| Fetch diff | 500ms | 1.8s |
| Parse diff | 300ms | 2.1s |
| Query patterns | 400ms | 2.5s |
| Execute 4 agents (parallel) | 15s | 17.5s |
| Synthesize results | 2s | 19.5s |
| Store in DB | 500ms | 20s |
| Post to GitHub | 1s | 21s |
| Update patterns | 3s (async) | 24s |
| **Total** | **~24s** | **24s** |

**Target:** <60s for 95% of reviews  
**Current:** ~24s average (well under target)

---

## Multi-Agent Architecture

### Agent Design Pattern

Each agent follows a consistent interface:

```python
from abc import ABC, abstractmethod
from typing import List
from models import Issue, CodeContext

class BaseAgent(ABC):
    """Base class for all review agents"""
    
    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.config = config
        self.agent_type = self.get_agent_type()
    
    @abstractmethod
    async def analyze(self, context: CodeContext) -> List[Issue]:
        """Analyze code and return issues"""
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """Return agent type identifier"""
        pass
    
    def confidence_score(self, issue: Issue) -> float:
        """Calculate confidence score for an issue"""
        base_score = 0.7
        
        # Boost if similar pattern was accepted before
        if issue.similar_pattern:
            acceptance_rate = issue.similar_pattern.acceptance_rate
            base_score += (acceptance_rate - 0.5) * 0.4
        
        return min(base_score, 1.0)
```

### Agent Implementations

#### Style Agent

**Focus:** Code formatting, conventions, structure

**Prompt Template:**
```python
STYLE_PROMPT = """
You are a code style reviewer. Analyze the following code changes for:

1. Naming conventions (consistent with language standards)
2. Function/method length (flag if >50 lines)
3. Code organization and structure
4. Documentation (docstrings, comments)
5. Import organization

Repository style preferences:
{style_preferences}

Code changes:
{code_diff}

Provide findings in JSON format:
{{
  "issues": [
    {{
      "line": 45,
      "severity": "suggestion",
      "message": "Function exceeds 50 lines, consider breaking into smaller functions",
      "suggestion": "Extract helper methods for distinct responsibilities"
    }}
  ]
}}
"""
```

**Execution Time:** ~2-3 seconds  
**Typical Findings:** 3-5 per PR

---

#### Security Agent

**Focus:** Vulnerability detection

**Prompt Template:**
```python
SECURITY_PROMPT = """
You are a security-focused code reviewer. Analyze for:

1. SQL injection vulnerabilities
2. XSS (Cross-Site Scripting) risks
3. Authentication/authorization bypasses
4. Hardcoded secrets (API keys, passwords)
5. Insecure data handling
6. Known vulnerable dependencies

CRITICAL: Only flag confirmed vulnerabilities, not theoretical risks.

Code changes:
{code_diff}

File context (surrounding code):
{file_context}

Return JSON with severity:
- "critical": Confirmed exploitable vulnerability
- "warning": Potential security risk
- "suggestion": Security best practice improvement
"""
```

**Execution Time:** ~4-5 seconds  
**Typical Findings:** 1-2 per PR (most PRs have 0)

---

#### Performance Agent

**Focus:** Algorithmic efficiency

**Checks:**
- Nested loops (O(n²) complexity)
- N+1 query problems in ORMs
- Inefficient data structures
- Blocking operations in async code
- Memory leaks (unclosed resources)

**Execution Time:** ~3-4 seconds  
**Typical Findings:** 2-3 per PR

---

#### Bug Detector Agent

**Focus:** Logic errors, edge cases

**Checks:**
- Null/undefined access
- Off-by-one errors
- Race conditions
- Missing error handling
- Type mismatches

**Execution Time:** ~3-4 seconds  
**Typical Findings:** 2-4 per PR

---

#### Synthesizer Agent

**Purpose:** Combine all findings into coherent review

**Process:**
1. Collect outputs from all agents
2. Deduplicate similar issues
3. Prioritize by severity × confidence
4. Format into readable review comment
5. Add summary statistics

**Deduplication Logic:**
```python
def deduplicate_issues(all_issues: List[Issue]) -> List[Issue]:
    """Remove duplicate/similar issues from different agents"""
    unique = []
    
    for issue in all_issues:
        # Check if similar issue already exists
        similar = find_similar(issue, unique, threshold=0.85)
        
        if similar:
            # Keep higher confidence version
            if issue.confidence > similar.confidence:
                unique.remove(similar)
                unique.append(issue)
        else:
            unique.append(issue)
    
    return unique

def find_similar(issue: Issue, existing: List[Issue], threshold: float) -> Optional[Issue]:
    """Find similar issue using embeddings"""
    if not existing:
        return None
    
    issue_embedding = generate_embedding(issue.message)
    
    for exist in existing:
        exist_embedding = generate_embedding(exist.message)
        similarity = cosine_similarity(issue_embedding, exist_embedding)
        
        if similarity > threshold and issue.line_number == exist.line_number:
            return exist
    
    return None
```

**Output Format:**
```markdown
## 🤖 AI Code Review

**Summary:** 12 issues found (2 critical, 5 warnings, 5 suggestions)  
**Processing time:** 45 seconds  
**Review ID:** #123

---

### 🔴 Critical Issues (2)

#### Security: SQL Injection Vulnerability
**File:** `src/auth/login.py` (Line 45)  
**Current code:**
```python
query = f"SELECT * FROM users WHERE username='{username}'"
```
**Issue:** User input is directly interpolated into SQL query, allowing SQL injection attacks.

**Recommendation:**
```python
query = "SELECT * FROM users WHERE username=%s"
cursor.execute(query, (username,))
```

**Confidence:** 95% | **Pattern match:** This team accepted similar fixes in 4/5 past cases

---

### ⚠️ Warnings (5)
...

### 💡 Suggestions (5)
...

---
*Review powered by AI Code Reviewer v1.0 | [Report issue](https://...)*
```

---

## Integration Patterns

### 1. GitHub Integration Pattern

**Authentication Flow:**
```
App Installation
      ↓
Generate JWT (private key)
      ↓
Exchange for Installation Token
      ↓
Cache token (50 min TTL)
      ↓
Use for API calls
      ↓
Refresh when expired
```

**Webhook Security:**
```python
def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify X-Hub-Signature-256 header"""
    expected = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    received = signature.replace("sha256=", "")
    
    return hmac.compare_digest(expected, received)
```

---

### 2. LLM Integration Pattern

**Retry with Exponential Backoff:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(anthropic.APIError)
)
async def call_claude_api(prompt: str) -> str:
    """Call Claude with retry logic"""
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

**Cost Tracking:**
```python
async def track_api_cost(prompt_tokens: int, completion_tokens: int):
    """Track costs in real-time"""
    cost = (prompt_tokens * 3 / 1_000_000) + (completion_tokens * 15 / 1_000_000)
    
    # Store in Redis counter
    today = datetime.now().date()
    await redis.incrbyfloat(f"cost:{today}", cost)
    
    # Check budget
    total_today = await redis.get(f"cost:{today}")
    if float(total_today) > DAILY_BUDGET:
        await alert_team(f"Daily budget exceeded: ${total_today}")
```

---

### 3. Vector Database Integration Pattern

**Embedding Generation with Caching:**
```python
async def get_embedding(text: str) -> List[float]:
    """Get embedding with Redis cache"""
    # Hash text for cache key
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    cache_key = f"embedding:{text_hash}"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Generate embedding
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    embedding = response.data[0].embedding
    
    # Cache for 7 days
    await redis.setex(cache_key, 7 * 24 * 3600, json.dumps(embedding))
    
    return embedding
```

**Pinecone Upsert Pattern:**
```python
async def store_pattern(pattern: Pattern, code: str):
    """Store pattern in both PostgreSQL and Pinecone"""
    # Generate embedding
    embedding = await get_embedding(code)
    
    # Store in PostgreSQL first
    db_pattern = await db.patterns.create(pattern)
    
    # Upsert to Pinecone
    vector_id = f"pattern_{db_pattern.id}"
    pinecone_index.upsert(vectors=[
        {
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "pattern_id": db_pattern.id,
                "repository_id": pattern.repository_id,
                "pattern_type": pattern.pattern_type,
                "language": pattern.language,
                "accepted": True,
                "votes": 1
            }
        }
    ])
    
    # Update PostgreSQL with vector_id
    await db.patterns.update(db_pattern.id, vector_id=vector_id)
```

---

## Scalability Design

### Horizontal Scaling Strategy

**Component Scaling:**

| Component | Scaling Method | Trigger | Max Instances |
|-----------|---------------|---------|---------------|
| FastAPI | Load balancer + auto-scale | CPU >70% | 10 |
| Celery Workers | Worker pool expansion | Queue depth >20 | 20 |
| PostgreSQL | Read replicas | Query latency >100ms | 3 replicas |
| Redis | Redis Cluster | Memory >80% | 6 nodes |

**Load Balancer Configuration (Nginx):**
```nginx
upstream fastapi_backend {
    least_conn;  # Route to least busy server
    server app1:8000 weight=1;
    server app2:8000 weight=1;
    server app3:8000 weight=1;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://fastapi_backend/health;
    }
}
```

---

### Database Scaling

**Read Replica Setup:**
```
Primary (Write)
    ↓
Streaming Replication
    ↓
┌──────────┬──────────┐
│ Replica1 │ Replica2 │
│  (Read)  │  (Read)  │
└──────────┴──────────┘
```

**Query Routing:**
```python
# Write queries → Primary
async def create_review(review_data):
    async with db.primary.transaction():
        return await db.reviews.create(review_data)

# Read queries → Replicas (round-robin)
async def get_review(review_id):
    replica = await db.get_read_replica()
    return await replica.reviews.get(review_id)
```

---

### Caching Strategy

**Multi-Level Cache:**
```
Request
  ↓
L1: Application Cache (in-memory, 1 min TTL)
  ↓ (miss)
L2: Redis Cache (5-60 min TTL)
  ↓ (miss)
L3: Database
```

**Cache Keys & TTLs:**
```python
CACHE_CONFIG = {
    "pr_metadata": 5 * 60,        # 5 minutes
    "file_contents": 60 * 60,     # 1 hour (immutable per SHA)
    "review_results": 10 * 60,    # 10 minutes
    "embeddings": 7 * 24 * 3600,  # 7 days
    "github_rate_limit": 60,      # 1 minute
}
```

---

## Security Architecture

### Defense in Depth

**Layer 1: Network Security**
- VPC isolation (database not publicly accessible)
- Security groups (whitelist IPs)
- TLS/SSL for all external communication

**Layer 2: Application Security**
- Webhook signature verification
- Input validation (Pydantic models)
- Rate limiting (per IP, per endpoint)
- SQL injection prevention (parameterized queries)

**Layer 3: Data Security**
- Encryption at rest (PostgreSQL, Redis)
- Encryption in transit (TLS 1.3)
- API keys in environment variables (never code)
- Secret rotation policy (quarterly)

**Layer 4: Access Control**
- GitHub App minimal permissions (read PRs, write comments)
- Database roles (read-only for analytics)
- API authentication (future: JWT tokens)

### Threat Mitigation

**Threat 1: Webhook Spoofing**
- Mitigation: HMAC signature verification
- Impact: Prevented

**Threat 2: Prompt Injection**
- Scenario: Malicious code in PR contains prompt injection
- Mitigation: Strict prompt templates, output validation
- Impact: Low (can't access data, only bias review)

**Threat 3: Data Breach**
- Mitigation: Encrypted storage, VPC isolation, minimal PII
- Impact: Low (we store minimal sensitive data)

**Threat 4: API Key Theft**
- Mitigation: Environment variables, rotation, monitoring
- Impact: Medium (unauthorized API usage)

**Threat 5: DDoS**
- Mitigation: Rate limiting, queue buffering, GitHub IP whitelist
- Impact: Low (delays reviews, doesn't expose data)

---

## Deployment Architecture

### Production Environment

```
┌─────────────────────────────────────────────┐
│           Cloud Provider (Railway)          │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │      Load Balancer (Nginx)         │    │
│  │  - SSL Termination                 │    │
│  │  - Health checks                   │    │
│  └────────────┬───────────────────────┘    │
│               │                             │
│       ┌───────┴────────┐                   │
│       │                │                    │
│  ┌────▼────┐      ┌───▼─────┐             │
│  │FastAPI 1│      │FastAPI 2│             │
│  │(2GB RAM)│      │(2GB RAM)│             │
│  └────┬────┘      └────┬────┘             │
│       │                │                    │
│       └────────┬───────┘                   │
│                │                            │
│  ┌─────────────▼──────────────────┐        │
│  │     Celery Workers (2x)         │        │
│  │  - Worker 1: Reviews            │        │
│  │  - Worker 2: Analytics          │        │
│  │  (2GB RAM each)                 │        │
│  └─────────────┬──────────────────┘        │
│                │                            │
│  ┌─────────────┴──────────────────┐        │
│  │      Data Services              │        │
│  │  ┌──────────┐  ┌──────────┐    │        │
│  │  │PostgreSQL│  │  Redis   │    │        │
│  │  │(4GB,20GB)│  │ (1GB)    │    │        │
│  │  └──────────┘  └──────────┘    │        │
│  └─────────────────────────────────┘        │
└─────────────────────────────────────────────┘

External Services:
┌──────────┐  ┌──────────┐  ┌──────────┐
│  GitHub  │  │ Anthropic│  │ Pinecone │
└──────────┘  └──────────┘  └──────────┘
```

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/reviewer
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  worker:
    build: .
    command: celery -A app.tasks worker --loglevel=info
    depends_on:
      - redis
      - db
  
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## Technology Decisions

### Decision Log

#### Why Event-Driven Architecture?

**Context:** Need to handle GitHub webhooks asynchronously

**Options:**
1. Synchronous processing (block webhook response)
2. Event-driven with queue
3. Serverless functions (AWS Lambda)

**Decision:** Event-driven with Celery

**Rationale:**
- GitHub webhooks timeout at 10s, we need 30-60s for review
- Queue decouples webhook receipt from processing
- Enables retry logic and monitoring
- More cost-effective than serverless for our scale

**Trade-offs:**
- More complex than synchronous (accepted)
- Requires Redis infrastructure (acceptable overhead)

---

#### Why LangGraph over Custom Orchestration?

**Context:** Need to coordinate multiple AI agents

**Options:**
1. Custom orchestration (manual agent chaining)
2. LangGraph
3. LangChain only (no graph)

**Decision:** LangGraph

**Rationale:**
- Built-in state management
- Conditional routing (skip agents based on PR size)
- Parallel execution support
- Visualization tools for debugging

**Trade-offs:**
- Learning curve
- Framework dependency
- Accepted: Benefits outweigh costs

---

## Appendix

### System Metrics Dashboard

**Key Metrics to Monitor:**

```
# Performance
review_duration_p50
review_duration_p95
review_duration_p99

# Throughput
reviews_per_hour
queue_depth
worker_utilization

# Quality
issue_acceptance_rate
false_positive_rate
agent_accuracy_by_type

# Cost
api_cost_per_review
daily_total_cost
cost_per_repository

# Reliability
error_rate
retry_rate
uptime_percentage
```

---

**Document Status:** ✅ Design Complete  
**Architecture Version:** v1.0  
**Last Updated:** January 2025  
**Change Log:** Initial architecture design
