# src_scaflog_zoho_mcp_server/auth.py

import time
from typing import Optional
import httpx
from pydantic import BaseModel, Field

from .config import ZohoCreatorConfig, API_BASE_URL

class TokenInfo(BaseModel):
    """Model for storing token information."""
    access_token: str
    expires_in: int
    created_at: float = Field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if the token is expired with a 5-minute buffer."""
        return time.time() > (self.created_at + self.expires_in - 300)

class ZohoAuth:
    """Handles authentication with Zoho Creator API."""
    def __init__(self, config: ZohoCreatorConfig):
        self.config = config
        self._token_info: Optional[TokenInfo] = None
        self._client = httpx.AsyncClient(timeout=30.0)

    async def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if not self._token_info or self._token_info.is_expired:
            await self._refresh_token()
        return self._token_info.access_token

    async def _refresh_token(self) -> None:
        """Refresh the access token using the refresh token."""
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        params = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": self.config.refresh_token,
            "grant_type": "refresh_token",
            "redirect_uri": "https://www.zohoapis.com"
        }

        async with self._client as client:
            response = await client.post(token_url, params=params)
            response.raise_for_status()
            data = response.json()

            self._token_info = TokenInfo(
                access_token=data["access_token"],
                expires_in=data["expires_in"]
            )

    async def get_authorized_headers(self) -> dict:
        """Get headers with authorization token."""
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()