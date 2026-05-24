import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import hmac
import hashlib
import json

client = TestClient(app)

def test_webhook_unauthorized():
    response = client.post("/api/webhooks/github", json={"action": "opened"})
    assert response.status_code == 401

def test_webhook_authorized():
    payload = {
        "action": "opened",
        "number": 1,
        "repository": {"id": 1, "name": "test", "full_name": "owner/test", "private": False},
        "sender": {"login": "user", "id": 1},
        "pull_request": {
            "id": 1,
            "number": 1,
            "state": "open",
            "title": "Test PR",
            "user": {"login": "user", "id": 1},
            "head": {"ref": "feature", "sha": "123"},
            "base": {"ref": "main", "sha": "456"},
            "diff_url": "https://github.com/owner/test/pull/1.diff"
        }
    }
    
    payload_bytes = json.dumps(payload).encode()
    mac = hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), msg=payload_bytes, digestmod=hashlib.sha256)
    signature = f"sha256={mac.hexdigest()}"
    
    response = client.post(
        "/api/webhooks/github", 
        json=payload,
        headers={"X-Hub-Signature-256": signature, "X-GitHub-Event": "pull_request"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
