from pathlib import Path
import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

class ZohoCreatorConfig(BaseModel):
    """Configuration for Zoho Creator API access."""
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    refresh_token: str = Field(..., description="OAuth refresh token")
    organization_id: str = Field(..., description="Zoho organization ID")
    environment: str = Field(default="production", description="Zoho environment (production/sandbox)")
    access_token: Optional[str] = Field(default=None, description="Current access token")

def load_config() -> ZohoCreatorConfig:
    """Load configuration from environment variables or .env file."""
    # Try to load from .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)

    return ZohoCreatorConfig(
        client_id=os.getenv("ZOHO_CLIENT_ID", ""),
        client_secret=os.getenv("ZOHO_CLIENT_SECRET", ""),
        refresh_token=os.getenv("ZOHO_REFRESH_TOKEN", ""),
        organization_id=os.getenv("ZOHO_ORGANIZATION_ID", ""),
        environment=os.getenv("ZOHO_ENVIRONMENT", "production"),
    )

# API endpoints for different environments
API_BASE_URL = {
    "production": "https://creator.zoho.com/api/v2/100rails/goscaffold",
    "sandbox": "https://creator.zoho.com/api/v2/sandbox"
}