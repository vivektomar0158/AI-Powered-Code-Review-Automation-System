# API Specification
## AI Code Review Agent

**Version:** 1.0  
**Author:** Vivek  
**Date:** January 2025  
**Base URL:** `https://api.code-reviewer.dev` (Production)  
**Base URL:** `http://localhost:8000` (Development)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Webhook Endpoints](#webhook-endpoints)
3. [Review Endpoints](#review-endpoints)
4. [Pull Request Endpoints](#pull-request-endpoints)
5. [Analytics Endpoints](#analytics-endpoints)
6. [Repository Configuration](#repository-configuration)
7. [Health & Status](#health--status)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Versioning](#versioning)

---

## Authentication

### GitHub App Authentication

The system operates as a GitHub App and uses installation access tokens.

**Token Acquisition Flow:**
1. Generate JWT using GitHub App private key
2. Exchange JWT for installation access token
3. Use access token for GitHub API calls (expires in 1 hour)

**Headers Required for GitHub API:**
```
Authorization: Bearer {installation_access_token}
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

### Webhook Authentication

**GitHub Webhook Signature Verification:**

All webhook requests include HMAC signature header:
```
X-Hub-Signature-256: sha256={signature}
```

**Verification Process:**
```
secret = WEBHOOK_SECRET from environment
computed_signature = HMAC-SHA256(request_body, secret)

if computed_signature == received_signature:
    process_webhook()
else:
    return 401 Unauthorized
```

### Future: API Key Authentication (Phase 2)

For dashboard/analytics access:
```
Authorization: Api-Key {your_api_key}
```

---

## Webhook Endpoints

### 1. GitHub Webhook Handler

Receives events from GitHub when PRs are created, updated, or closed.

**Endpoint:**
```
POST /api/webhooks/github
```

**Headers:**
```
Content-Type: application/json
X-GitHub-Event: pull_request
X-GitHub-Delivery: {unique_delivery_id}
X-Hub-Signature-256: sha256={signature}
User-Agent: GitHub-Hookshot/{version}
```

**Request Body (Pull Request Opened):**
```json
{
  "action": "opened",
  "number": 42,
  "pull_request": {
    "id": 1234567890,
    "number": 42,
    "state": "open",
    "title": "Add user authentication feature",
    "user": {
      "login": "developer123",
      "id": 98765
    },
    "head": {
      "ref": "feature/auth",
      "sha": "abc123def456"
    },
    "base": {
      "ref": "main",
      "sha": "xyz789"
    },
    "diff_url": "https://github.com/owner/repo/pull/42.diff",
    "changed_files": 5,
    "additions": 120,
    "deletions": 30
  },
  "repository": {
    "id": 123456,
    "name": "awesome-project",
    "full_name": "owner/awesome-project",
    "private": false
  }
}
```

**Supported Actions:**
- `opened` - New PR created, trigger full review
- `synchronize` - New commits pushed, review changed files
- `reopened` - PR reopened, re-trigger review
- `ready_for_review` - Draft converted to ready, trigger review

**Response:**
```json
{
  "status": "accepted",
  "message": "Webhook received, review queued",
  "review_id": null,
  "estimated_time_seconds": 45
}
```

**Status Codes:**
- `200 OK` - Webhook accepted and queued
- `202 Accepted` - Webhook received but not processed (duplicate/irrelevant action)
- `401 Unauthorized` - Invalid signature
- `400 Bad Request` - Malformed payload
- `500 Internal Server Error` - System error (will retry)

**Idempotency:**
GitHub may send duplicate webhooks. System deduplicates using:
```
Key: webhook:{pr_id}:{commit_sha}:{action}
TTL: 1 hour
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-Hub-Signature-256: sha256=abcdef..." \
  -d @webhook_payload.json
```

---

## Review Endpoints

### 2. Get Review by ID

Retrieve details of a specific review.

**Endpoint:**
```
GET /api/reviews/{review_id}
```

**Path Parameters:**
- `review_id` (integer, required) - Unique review identifier

**Response (Success):**
```json
{
  "id": 123,
  "pull_request_id": 456,
  "status": "completed",
  "total_issues": 12,
  "critical_issues": 2,
  "warnings": 5,
  "suggestions": 5,
  "processing_time_ms": 45230,
  "cost_usd": 0.12,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:45Z",
  "agents_executed": [
    "style",
    "security",
    "performance",
    "bug"
  ],
  "github_review_url": "https://github.com/owner/repo/pull/42#pullrequestreview-987654321"
}
```

**Response (In Progress):**
```json
{
  "id": 123,
  "status": "processing",
  "total_issues": null,
  "processing_time_ms": null,
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:31:00Z",
  "progress": {
    "stage": "agent_execution",
    "agents_completed": ["style", "security"],
    "agents_remaining": ["performance", "bug"]
  }
}
```

**Status Codes:**
- `200 OK` - Review found
- `404 Not Found` - Review ID doesn't exist
- `500 Internal Server Error` - Database error

**Example:**
```bash
curl http://localhost:8000/api/reviews/123
```

---

### 3. Get Review Comments

Retrieve all comments posted by agents for a specific review.

**Endpoint:**
```
GET /api/reviews/{review_id}/comments
```

**Query Parameters:**
- `severity` (string, optional) - Filter by severity: `critical`, `warning`, `suggestion`
- `agent_type` (string, optional) - Filter by agent: `style`, `security`, `performance`, `bug`
- `accepted` (boolean, optional) - Filter by acceptance status
- `limit` (integer, optional, default: 50) - Max results per page
- `offset` (integer, optional, default: 0) - Pagination offset

**Response:**
```json
{
  "comments": [
    {
      "id": 789,
      "review_id": 123,
      "file_path": "src/auth/login.py",
      "line_number": 45,
      "agent_type": "security",
      "severity": "critical",
      "message": "SQL injection vulnerability detected. User input is directly concatenated into SQL query without sanitization.",
      "code_snippet": "query = f\"SELECT * FROM users WHERE username='{username}'\"",
      "suggestion": "Use parameterized queries:\n```python\nquery = \"SELECT * FROM users WHERE username=%s\"\ncursor.execute(query, (username,))\n```",
      "confidence_score": 0.95,
      "accepted": true,
      "github_comment_id": 987654321,
      "created_at": "2024-01-15T10:30:45Z"
    },
    {
      "id": 790,
      "agent_type": "style",
      "severity": "suggestion",
      "message": "Function exceeds recommended length (62 lines). Consider breaking into smaller functions.",
      "confidence_score": 0.72,
      "accepted": false,
      "created_at": "2024-01-15T10:30:45Z"
    }
  ],
  "pagination": {
    "total": 12,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

**Status Codes:**
- `200 OK` - Comments retrieved
- `404 Not Found` - Review not found
- `400 Bad Request` - Invalid query parameters

**Example:**
```bash
# Get all critical security issues
curl "http://localhost:8000/api/reviews/123/comments?severity=critical&agent_type=security"
```

---

### 4. Retry Failed Review

Re-trigger a failed review.

**Endpoint:**
```
POST /api/reviews/{review_id}/retry
```

**Request Body:**
```json
{
  "retry_all_agents": true
}
```

**Response:**
```json
{
  "status": "queued",
  "new_review_id": 124,
  "message": "Review retry queued successfully",
  "estimated_time_seconds": 45
}
```

**Status Codes:**
- `202 Accepted` - Retry queued
- `404 Not Found` - Review not found
- `409 Conflict` - Review already completed (can't retry)
- `429 Too Many Requests` - Rate limit exceeded

---

## Pull Request Endpoints

### 5. List Reviews for a Pull Request

Get all reviews for a specific PR.

**Endpoint:**
```
GET /api/pull-requests/{pr_id}/reviews
```

**Query Parameters:**
- `status` (string, optional) - Filter by status: `pending`, `processing`, `completed`, `failed`
- `limit` (integer, optional, default: 10)
- `offset` (integer, optional, default: 0)

**Response:**
```json
{
  "pull_request": {
    "id": 456,
    "number": 42,
    "title": "Add user authentication",
    "repository": "owner/awesome-project",
    "state": "open"
  },
  "reviews": [
    {
      "id": 123,
      "status": "completed",
      "total_issues": 12,
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:30:45Z"
    },
    {
      "id": 122,
      "status": "completed",
      "total_issues": 8,
      "created_at": "2024-01-14T15:20:00Z",
      "note": "Review after first commit"
    }
  ],
  "pagination": {
    "total": 2,
    "limit": 10,
    "offset": 0
  }
}
```

**Status Codes:**
- `200 OK` - Reviews retrieved
- `404 Not Found` - PR not found

---

### 6. Get Pull Request Details

Retrieve PR metadata stored in our system.

**Endpoint:**
```
GET /api/pull-requests/{pr_id}
```

**Response:**
```json
{
  "id": 456,
  "github_id": 1234567890,
  "repository": {
    "id": 123,
    "name": "awesome-project",
    "full_name": "owner/awesome-project"
  },
  "number": 42,
  "title": "Add user authentication feature",
  "author": "developer123",
  "state": "open",
  "base_branch": "main",
  "head_branch": "feature/auth",
  "diff_url": "https://github.com/owner/repo/pull/42.diff",
  "files_changed": 5,
  "additions": 120,
  "deletions": 30,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "latest_review": {
    "id": 123,
    "status": "completed",
    "total_issues": 12
  }
}
```

**Status Codes:**
- `200 OK` - PR found
- `404 Not Found` - PR not found

---

## Analytics Endpoints

### 7. Repository Summary

Get aggregate statistics for a repository.

**Endpoint:**
```
GET /api/analytics/repository/{repo_id}/summary
```

**Query Parameters:**
- `start_date` (ISO 8601 date, optional) - Start of date range
- `end_date` (ISO 8601 date, optional) - End of date range
- `granularity` (string, optional) - `day`, `week`, `month` (default: `week`)

**Response:**
```json
{
  "repository": {
    "id": 123,
    "name": "awesome-project",
    "full_name": "owner/awesome-project"
  },
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "summary": {
    "total_reviews": 150,
    "total_prs_reviewed": 148,
    "avg_processing_time_ms": 42000,
    "avg_issues_per_review": 8.2,
    "total_cost_usd": 18.50,
    "acceptance_rate": 0.82
  },
  "issues_by_severity": {
    "critical": 45,
    "warning": 120,
    "suggestion": 280
  },
  "issues_by_agent": {
    "style": 180,
    "security": 65,
    "performance": 95,
    "bug": 105
  },
  "top_issue_types": [
    {
      "type": "style.naming_convention",
      "count": 35,
      "acceptance_rate": 0.89
    },
    {
      "type": "security.sql_injection",
      "count": 12,
      "acceptance_rate": 0.95
    },
    {
      "type": "performance.nested_loops",
      "count": 28,
      "acceptance_rate": 0.71
    }
  ],
  "time_series": [
    {
      "date": "2024-01-01",
      "reviews": 5,
      "avg_issues": 7.4
    },
    {
      "date": "2024-01-08",
      "reviews": 12,
      "avg_issues": 8.1
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Analytics retrieved
- `404 Not Found` - Repository not found
- `400 Bad Request` - Invalid date range

**Example:**
```bash
curl "http://localhost:8000/api/analytics/repository/123/summary?start_date=2024-01-01&end_date=2024-01-31"
```

---

### 8. Agent Performance

Analyze individual agent accuracy and performance.

**Endpoint:**
```
GET /api/analytics/agents/performance
```

**Query Parameters:**
- `repo_id` (integer, optional) - Filter by repository
- `start_date` (ISO 8601, optional)
- `end_date` (ISO 8601, optional)

**Response:**
```json
{
  "agents": [
    {
      "agent_type": "security",
      "total_issues_raised": 65,
      "critical_issues": 15,
      "acceptance_rate": 0.92,
      "avg_confidence_score": 0.88,
      "avg_processing_time_ms": 3200,
      "false_positive_rate": 0.08,
      "top_patterns": [
        "sql_injection",
        "xss_vulnerability",
        "hardcoded_secrets"
      ]
    },
    {
      "agent_type": "style",
      "total_issues_raised": 180,
      "acceptance_rate": 0.75,
      "avg_confidence_score": 0.68,
      "avg_processing_time_ms": 2100
    }
  ],
  "overall_metrics": {
    "total_issues": 445,
    "avg_acceptance_rate": 0.82,
    "avg_processing_time_ms": 2800
  }
}
```

---

### 9. Cost Analysis

Track API usage and costs.

**Endpoint:**
```
GET /api/analytics/costs
```

**Query Parameters:**
- `start_date` (ISO 8601, required)
- `end_date` (ISO 8601, required)
- `granularity` (string, optional) - `day`, `week`, `month`

**Response:**
```json
{
  "date_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "total_cost_usd": 27.50,
  "breakdown": {
    "claude_api": 24.30,
    "openai_embeddings": 0.20,
    "pinecone": 0.00
  },
  "cost_per_review_avg": 0.18,
  "reviews_total": 150,
  "daily_costs": [
    {
      "date": "2024-01-01",
      "cost_usd": 0.85,
      "reviews": 5
    }
  ],
  "budget_status": {
    "monthly_budget_usd": 50.00,
    "spent_usd": 27.50,
    "remaining_usd": 22.50,
    "percent_used": 55
  },
  "alerts": []
}
```

**Budget Alert Example:**
```json
{
  "alerts": [
    {
      "level": "warning",
      "message": "Daily cost exceeded $2.00 on 2024-01-15",
      "date": "2024-01-15",
      "actual_cost": 2.35
    }
  ]
}
```

---

## Repository Configuration

### 10. Get Repository Config

Retrieve the parsed `.ai-review.yml` configuration for a repository.

**Endpoint:**
```
GET /api/repositories/{repo_id}/config
```

**Response:**
```json
{
  "repository_id": 123,
  "config": {
    "enabled": true,
    "agents": {
      "style": {
        "enabled": true,
        "severity_threshold": "warning"
      },
      "security": {
        "enabled": true,
        "severity_threshold": "suggestion"
      },
      "performance": {
        "enabled": true,
        "severity_threshold": "warning"
      },
      "bug": {
        "enabled": false
      }
    },
    "rules": {
      "max_function_length": 50,
      "require_docstrings": true,
      "exclude_paths": [
        "tests/",
        "migrations/",
        "*.min.js"
      ]
    },
    "review_scope": "changed_files_only",
    "auto_comment": true,
    "learning_enabled": true
  },
  "last_updated": "2024-01-10T08:00:00Z",
  "source": "repository_file"
}
```

**Status Codes:**
- `200 OK` - Config retrieved (or defaults if no .ai-review.yml)
- `404 Not Found` - Repository not found

---

### 11. Update Repository Config (Future)

Modify repository settings via API.

**Endpoint:**
```
PATCH /api/repositories/{repo_id}/config
```

**Request Body:**
```json
{
  "agents": {
    "bug": {
      "enabled": true
    }
  },
  "rules": {
    "max_function_length": 75
  }
}
```

**Response:**
```json
{
  "status": "updated",
  "config": { /* updated config */ }
}
```

---

## Health & Status

### 12. Health Check

System health status for monitoring.

**Endpoint:**
```
GET /health
```

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 12
    },
    "redis": {
      "status": "ok",
      "latency_ms": 3
    },
    "celery": {
      "status": "ok",
      "active_workers": 2,
      "queue_depth": 5
    },
    "github_api": {
      "status": "ok",
      "rate_limit_remaining": 4850
    },
    "claude_api": {
      "status": "ok"
    }
  }
}
```

**Response (Degraded):**
```json
{
  "status": "degraded",
  "checks": {
    "database": {
      "status": "ok"
    },
    "redis": {
      "status": "error",
      "message": "Connection timeout",
      "latency_ms": null
    }
  }
}
```

**Status Codes:**
- `200 OK` - System healthy
- `503 Service Unavailable` - Critical component down

**Use Cases:**
- Load balancer health checks
- Kubernetes liveness/readiness probes
- Monitoring dashboards

---

### 13. System Metrics

Prometheus-compatible metrics endpoint.

**Endpoint:**
```
GET /metrics
```

**Response (Prometheus format):**
```
# HELP review_duration_seconds Time taken to complete review
# TYPE review_duration_seconds histogram
review_duration_seconds_bucket{status="completed",le="30"} 45
review_duration_seconds_bucket{status="completed",le="60"} 120
review_duration_seconds_bucket{status="completed",le="120"} 145
review_duration_seconds_count{status="completed"} 150
review_duration_seconds_sum{status="completed"} 6300

# HELP review_cost_usd Cost per review in USD
# TYPE review_cost_usd counter
review_cost_usd{agent="style"} 4.50
review_cost_usd{agent="security"} 6.20

# HELP webhook_events_total Total webhook events received
# TYPE webhook_events_total counter
webhook_events_total{event_type="pull_request.opened"} 150
webhook_events_total{event_type="pull_request.synchronize"} 280
```

---

## Error Handling

### Error Response Format

All errors follow consistent structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "start_date",
      "issue": "Date format must be ISO 8601"
    },
    "request_id": "req_abc123def456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request parameters |
| 400 | `MALFORMED_PAYLOAD` | Request body is not valid JSON |
| 401 | `INVALID_SIGNATURE` | Webhook signature verification failed |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 404 | `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| 409 | `CONFLICT` | Resource state conflict (e.g., retry completed review) |
| 422 | `UNPROCESSABLE_ENTITY` | Valid format but semantically incorrect |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 502 | `UPSTREAM_ERROR` | External service (GitHub, Claude) error |
| 503 | `SERVICE_UNAVAILABLE` | System temporarily down |
| 504 | `TIMEOUT` | Request processing timeout |

### Example Error Responses

**Validation Error (400):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "start_date must be before end_date",
    "details": {
      "start_date": "2024-01-31",
      "end_date": "2024-01-01"
    },
    "request_id": "req_xyz789"
  }
}
```

**Rate Limit (429):**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded. Retry after 60 seconds.",
    "retry_after": 60,
    "limit": 100,
    "reset_at": "2024-01-15T11:00:00Z"
  }
}
```

**Upstream Error (502):**
```json
{
  "error": {
    "code": "UPSTREAM_ERROR",
    "message": "GitHub API is temporarily unavailable",
    "upstream_service": "github",
    "retry_recommended": true
  }
}
```

---

## Rate Limiting

### Limits

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| Webhooks | 1000 requests | per hour |
| Review APIs | 100 requests | per minute |
| Analytics | 50 requests | per minute |
| Health Check | Unlimited | - |

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705318800
```

### Exceeding Limits

When limit exceeded:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after": 45
  }
}
```

Response includes:
- HTTP 429 status
- `Retry-After` header (seconds)
- Reset timestamp

---

## Versioning

### API Versioning Strategy

**Current:** v1 (implicit, no version in URL)

**Future:** Version in URL path
```
/api/v2/reviews/{id}
```

**Header-Based Versioning (Alternative):**
```
Accept: application/vnd.code-reviewer.v2+json
```

### Breaking Changes Policy

- **Minor version:** Backward compatible additions
- **Major version:** Breaking changes
- **Deprecation:** 6 months notice, documented in headers

**Deprecation Header:**
```
Deprecation: true
Sunset: Sat, 31 Jul 2024 23:59:59 GMT
Link: <https://docs.code-reviewer.dev/migration/v2>; rel="deprecation"
```

---

## Request/Response Examples

### Complete Workflow Example

**1. PR Created → Webhook Received**
```bash
# GitHub sends webhook
POST /api/webhooks/github
X-Hub-Signature-256: sha256=abc...
{
  "action": "opened",
  "pull_request": { "number": 42, ... }
}

# Response
200 OK
{
  "status": "accepted",
  "review_id": null,
  "estimated_time_seconds": 45
}
```

**2. Check Review Status (30s later)**
```bash
GET /api/pull-requests/456/reviews

# Response
200 OK
{
  "reviews": [
    {
      "id": 123,
      "status": "processing",
      "progress": {
        "stage": "agent_execution",
        "agents_completed": ["style", "security"]
      }
    }
  ]
}
```

**3. Review Completed (60s later)**
```bash
GET /api/reviews/123

# Response
200 OK
{
  "id": 123,
  "status": "completed",
  "total_issues": 12,
  "critical_issues": 2,
  "processing_time_ms": 45230,
  "github_review_url": "https://github.com/..."
}
```

**4. View Issues**
```bash
GET /api/reviews/123/comments?severity=critical

# Response
200 OK
{
  "comments": [
    {
      "severity": "critical",
      "message": "SQL injection vulnerability",
      "file_path": "auth/login.py",
      "line_number": 45,
      "suggestion": "Use parameterized queries..."
    }
  ]
}
```

---

## OpenAPI / Swagger Documentation

### Auto-Generated Docs

FastAPI automatically generates interactive documentation:

**Swagger UI:**
```
http://localhost:8000/docs
```

**ReDoc:**
```
http://localhost:8000/redoc
```

**OpenAPI JSON Schema:**
```
http://localhost:8000/openapi.json
```

### Features
- ✅ Try API endpoints directly in browser
- ✅ Auto-populated request examples
- ✅ Schema validation documentation
- ✅ Authentication flow documentation

---

## Best Practices for API Consumers

### 1. Always Check Status Codes
Don't assume 200. Handle 4xx and 5xx appropriately.

### 2. Implement Exponential Backoff
For 429, 502, 503 errors:
```
Wait time = min(base * 2^retry_count, max_wait)
```

### 3. Use Request IDs for Debugging
Include `X-Request-ID` header in support requests.

### 4. Cache Aggressively
Review data rarely changes. Cache for 5-10 minutes.

### 5. Webhook Signature Verification
Always verify `X-Hub-Signature-256` before processing.

### 6. Monitor Rate Limits
Track `X-RateLimit-Remaining` header proactively.

---

## Future API Enhancements

### Planned (Phase 2)

1. **GraphQL Endpoint** - More flexible querying
2. **Webhook Subscriptions** - Custom webhook events
3. **Batch Operations** - Review multiple PRs in one request
4. **Export API** - Download review data (CSV, JSON)
5. **Real-time WebSocket** - Live review progress updates

### Under Consideration

- OAuth 2.0 for third-party integrations
- Pagination cursors (instead of offset-based)
- Field filtering (?fields=id,status,total_issues)
- Webhook retry configuration API

---

## Appendix

### Common Query Patterns

**Get all critical issues for last 7 days:**
```bash
curl "http://localhost:8000/api/analytics/repository/123/summary?start_date=2024-01-08&end_date=2024-01-15" \
  | jq '.issues_by_severity.critical'
```

**Find reviews that took >60 seconds:**
```sql
-- Direct database query for analytics
SELECT id, processing_time_ms 
FROM reviews 
WHERE processing_time_ms > 60000
ORDER BY processing_time_ms DESC;
```

**Check if review is done (polling):**
```bash
while true; do
  status=$(curl -s http://localhost:8000/api/reviews/123 | jq -r '.status')
  if [ "$status" = "completed" ]; then
    echo "Review done!"
    break
  fi
  sleep 5
done
```

---

**Document Status:** ✅ Ready for Implementation  
**API Version:** v1.0  
**Last Updated:** January 2025  
**Change Log:** Initial API specification
