# tests/conftest.py
import pytest
from unittest.mock import AsyncMock
from typing import AsyncGenerator, Generator
import httpx
from datetime import datetime
import os
from pathlib import Path
import sys
from dotenv import load_dotenv  # Import dotenv to load environment variables
import logging  # Import logging

# Import the necessary classes
from scaflog_zoho_mcp_server.config import ZohoCreatorConfig
from scaflog_zoho_mcp_server.auth import ZohoAuth
from scaflog_zoho_mcp_server.service import ZohoCreatorService
from mcp import ClientSession, StdioServerParameters  # Add this import
from mcp.client.stdio import stdio_client  # Add this import

# Configure logging to write to a file
logging.basicConfig(
    filename='app.log',  # Specify the log file name
    filemode='a',        # Append mode
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO   # Set the logging level
)

# Log that the tests are starting
logging.info("Starting tests...")

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(scope="session")
def test_env() -> Generator[dict, None, None]:
    """Create a test environment with necessary configuration."""
    env = {
        "ZOHO_CLIENT_ID": os.getenv("ZOHO_CLIENT_ID"),
        "ZOHO_CLIENT_SECRET": os.getenv("ZOHO_CLIENT_SECRET"),
        "ZOHO_REFRESH_TOKEN": os.getenv("ZOHO_REFRESH_TOKEN"),
        "ZOHO_ORGANIZATION_ID": os.getenv("ZOHO_ORGANIZATION_ID"),
        "ZOHO_ENVIRONMENT": os.getenv("ZOHO_ENVIRONMENT"),
    }
    
    yield env

@pytest.fixture
async def mock_service() -> AsyncGenerator[ZohoCreatorService, None]:
    """Create a service with actual data from Zoho Creator."""
    config = ZohoCreatorConfig(
        client_id=os.getenv("ZOHO_CLIENT_ID"),
        client_secret=os.getenv("ZOHO_CLIENT_SECRET"),
        refresh_token=os.getenv("ZOHO_REFRESH_TOKEN"),
        organization_id=os.getenv("ZOHO_ORGANIZATION_ID"),
        environment=os.getenv("ZOHO_ENVIRONMENT")
    )
    auth = ZohoAuth(config)
    
    # Create a new instance of ZohoCreatorService
    service = ZohoCreatorService(auth)

    # Create a new HTTP client for each test
    service._client = httpx.AsyncClient()  # Create a new client instance

    yield service

    await service._client.aclose()  # Close the client after the test
    await service.close()  # Close the service

@pytest.fixture
async def client_session(test_env) -> AsyncGenerator[ClientSession, None]:
    """Create a client session connected to the test server."""
    python_path = sys.executable
    project_root = Path(__file__).parent.parent
    
    server_params = StdioServerParameters(
        command=python_path,
        args=["-m", "src"],
        env={
            **os.environ,
            **test_env,
            "PYTHONPATH": str(project_root)
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
