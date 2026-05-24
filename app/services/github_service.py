import time
import httpx
import logging
import jwt
import os
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class GitHubService:
    """Service to interact with GitHub API using App Authentication."""
    
    def __init__(self):
        self.app_id = settings.GITHUB_APP_ID
        self.base_url = "https://api.github.com"
        self._tokens: Dict[int, Dict] = {}
        
        # Load private key
        key_str = self._load_private_key()
        if key_str:
            try:
                self.private_key = load_pem_private_key(
                    key_str.encode() if isinstance(key_str, str) else key_str,
                    password=None
                )
                logger.info("GitHub App private key loaded successfully.")
            except Exception as e:
                self.private_key = None
                logger.error(f"Failed to load GitHub private key: {e}")
        else:
            self.private_key = None
            logger.warning("GitHub private key not found. GitHub integration will not work.")

    def _load_private_key(self) -> Optional[str]:
        """Load private key from file or base64 env var."""
        # Try base64 first
        if settings.GITHUB_PRIVATE_KEY_BASE64:
            import base64
            return base64.b64decode(settings.GITHUB_PRIVATE_KEY_BASE64).decode("utf-8")
        
        # Try file path
        key_path = settings.GITHUB_PRIVATE_KEY_PATH
        if key_path and os.path.exists(key_path):
            with open(key_path, "r") as f:
                return f.read()
        
        logger.error(f"Private key file not found at: {key_path}")
        return None

    def _generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication."""
        if not self.private_key:
            raise RuntimeError("GitHub private key not loaded")
        if not self.app_id:
            raise RuntimeError("GITHUB_APP_ID not set in .env")
            
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (10 * 60),
            "iss": str(self.app_id)
        }
        
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        pem = self.private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
        return jwt.encode(payload, pem, algorithm="RS256")

    async def _get_installation_id(self, repo_full_name: str) -> Optional[int]:
        """Fetch the installation ID for a repository."""
        jwt_token = self._generate_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        logger.info(f"Fetching installation ID for {repo_full_name}")
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo_full_name}/installation",
                headers=headers
            )
            
            if response.status_code == 200:
                iid = response.json().get("id")
                logger.info(f"Installation ID for {repo_full_name}: {iid}")
                return iid
            else:
                logger.error(f"Failed to get installation ID: {response.status_code} {response.text}")
                return None

    async def _get_installation_token(self, repo_full_name: str) -> str:
        """Get or create an installation access token."""
        installation_id = await self._get_installation_id(repo_full_name)
        if not installation_id:
            raise ValueError(f"GitHub App not installed on {repo_full_name}. Go to your GitHub App settings and install it.")

        # Check cache
        cached = self._tokens.get(installation_id)
        if cached and time.time() < cached["expires_at"] - 300:
            return cached["token"]

        jwt_token = self._generate_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/app/installations/{installation_id}/access_tokens",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            
            self._tokens[installation_id] = {
                "token": data["token"],
                "expires_at": time.time() + 3600
            }
            logger.info(f"Got installation token for {repo_full_name}")
            return data["token"]

    async def _make_request(self, method: str, url: str, repo_full_name: str, **kwargs) -> httpx.Response:
        token = await self._get_installation_token(repo_full_name)
        headers = kwargs.pop("headers", {})
        headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        })
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await client.request(method, f"{self.base_url}{url}", headers=headers, **kwargs)

    async def fetch_pull_request(self, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        logger.info(f"Fetching PR {repo_full_name}#{pr_number}")
        response = await self._make_request("GET", f"/repos/{repo_full_name}/pulls/{pr_number}", repo_full_name)
        response.raise_for_status()
        return response.json()

    async def fetch_diff(self, repo_full_name: str, pr_number: int) -> str:
        logger.info(f"Fetching diff for {repo_full_name}#{pr_number}")
        token = await self._get_installation_token(repo_full_name)
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.diff"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo_full_name}/pulls/{pr_number}",
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"Diff fetched: {len(response.text)} chars")
            return response.text

    async def post_review(self, repo_full_name: str, pr_number: int, body: str) -> str:
        logger.info(f"Posting review to {repo_full_name}#{pr_number}")
        payload = {
            "body": body,
            "event": "COMMENT"
        }
        
        response = await self._make_request(
            "POST",
            f"/repos/{repo_full_name}/pulls/{pr_number}/reviews",
            repo_full_name,
            json=payload
        )
        response.raise_for_status()
        url = response.json().get("html_url", "")
        logger.info(f"Review posted successfully: {url}")
        return url

github_service = GitHubService()
