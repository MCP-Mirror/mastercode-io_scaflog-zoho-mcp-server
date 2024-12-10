# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Generator
import httpx
from datetime import datetime
import os
from pathlib import Path
import tempfile
import sys

import mcp.types as types
from src.config import ZohoCreatorConfig
from src.auth import ZohoAuth
from src.service import ZohoCreatorService
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.fixture(scope="session")
def test_env() -> Generator[dict, None, None]:
    """Create a test environment with necessary configuration."""
    env = {
        "ZOHO_CLIENT_ID": "test_client_id",
        "ZOHO_CLIENT_SECRET": "test_client_secret",
        "ZOHO_REFRESH_TOKEN": "test_refresh_token",
        "ZOHO_ORGANIZATION_ID": "test_org_id",
        "ZOHO_ENVIRONMENT": "sandbox",
    }
    
    # Create a temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        for key, value in env.items():
            f.write(f"{key}={value}\n")
    
    # Set the env var to point to our temp file
    os.environ["ENV_FILE"] = f.name
    
    yield env
    
    # Cleanup
    Path(f.name).unlink()

@pytest.fixture
async def mock_service() -> AsyncGenerator[ZohoCreatorService, None]:
    """Create a mock service with test data."""
    config = ZohoCreatorConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        organization_id="test_org_id",
        environment="sandbox"
    )
    auth = ZohoAuth(config)
    auth.get_authorized_headers = AsyncMock(return_value={
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    })
    
    service = ZohoCreatorService(auth)
    
    # Mock the HTTP client
    client = AsyncMock(spec=httpx.AsyncClient)
    service._client = client

    # Create mock response data
    mock_forms_data = {
        "forms": [
            {
                "link_name": "test_form",
                "display_name": "Test Form",
                "access_type": "read"
            }
        ]
    }

    mock_fields_data = {
        "fields": [
            {
                "api_name": "test_field",
                "display_name": "Test Field",
                "type": "text",
                "required": True
            }
        ]
    }

    mock_record_data = {
        "record": {
            "ID": "123",
            "Created_Time": "2024-01-01T00:00:00Z",
            "Modified_Time": "2024-01-01T00:00:00Z",
            "test_field": "test_value"
        }
    }

    mock_records_data = {
        "records": [mock_record_data["record"]]
    }

    # Create mock responses
    forms_response = MagicMock(spec=httpx.Response)
    forms_response.json = AsyncMock(return_value=mock_forms_data)
    forms_response.raise_for_status = MagicMock()

    fields_response = MagicMock(spec=httpx.Response)
    fields_response.json = AsyncMock(return_value=mock_fields_data)
    fields_response.raise_for_status = MagicMock()

    records_response = MagicMock(spec=httpx.Response)
    records_response.json = AsyncMock(return_value=mock_records_data)
    records_response.raise_for_status = MagicMock()

    record_response = MagicMock(spec=httpx.Response)
    record_response.json = AsyncMock(return_value=mock_record_data)
    record_response.raise_for_status = MagicMock()

    # Setup client mocks
    client.get = AsyncMock(side_effect=lambda url, **kwargs: 
        forms_response if url.endswith("/forms") else
        fields_response if "fields" in url else
        records_response if "records" in url else
        record_response
    )
    client.post = AsyncMock(return_value=record_response)
    client.patch = AsyncMock(return_value=record_response)
    
    yield service
    await service.close()

@pytest.fixture
async def client_session(test_env) -> AsyncGenerator[ClientSession, None]:
    """Create a client session connected to the test server."""
    # Use sys.executable to get the path to the current Python interpreter
    python_path = sys.executable
    
    # Get the absolute path to the project root
    project_root = Path(__file__).parent.parent
    
    server_params = StdioServerParameters(
        command=python_path,  # Use full path to Python
        args=["-m", "src"],
        env={
            **os.environ,  # Include current environment
            **test_env,    # Add our test environment
            "PYTHONPATH": str(project_root)  # Add project root to Python path
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
