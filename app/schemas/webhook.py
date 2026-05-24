from pydantic import BaseModel, Field
from typing import Optional, Any

class GitHubUser(BaseModel):
    login: str
    id: int

class GitHubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool

class PullRequestCommitRef(BaseModel):
    ref: str
    sha: str

class PullRequestDetails(BaseModel):
    id: int
    number: int
    state: str
    title: str
    user: GitHubUser
    head: PullRequestCommitRef
    base: PullRequestCommitRef
    diff_url: str
    changed_files: Optional[int] = 0
    additions: Optional[int] = 0
    deletions: Optional[int] = 0

class WebhookPayload(BaseModel):
    action: str
    number: Optional[int] = None
    pull_request: Optional[PullRequestDetails] = None
    repository: GitHubRepo
    sender: GitHubUser
    
    # Allow extra fields since GitHub sends a lot of data we might not explicitly map
    class Config:
        extra = "allow"
