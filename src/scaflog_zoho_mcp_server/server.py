# src_scaflog_zoho_mcp_server/server.py

import json
import logging
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse
from pydantic import AnyUrl

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .config import load_config, API_BASE_URL
from .auth import ZohoAuth
from .service import ZohoCreatorService
from .resource_config import WHITELISTED_RESOURCES

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a server instance
server = Server("scaflog-zoho-mcp-server")
config = load_config()
auth = ZohoAuth(config)
service = ZohoCreatorService(auth)

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available whitelisted Zoho Creator forms and reports as resources."""
    logger.debug("Starting handle_list_resources...")
    
    try:
        resources = []
        
        # Add container resources
        resources.append(
            types.Resource(
                uri=AnyUrl("zoho://forms"),
                name="Available Forms",
                description="List of available Zoho Creator forms",
                mimeType="application/json"
            )
        )
        
        resources.append(
            types.Resource(
                uri=AnyUrl("zoho://reports"),
                name="Available Reports",
                description="List of available Zoho Creator reports",
                mimeType="application/json"
            )
        )
        
        # Add whitelisted forms
        for link_name, form_config in WHITELISTED_RESOURCES["forms"].items():
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"zoho://form/{link_name}"),
                    name=form_config.display_name,
                    description=form_config.description,
                    mimeType="application/json"
                )
            )
        
        # Add whitelisted reports
        for link_name, report_config in WHITELISTED_RESOURCES["reports"].items():
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"zoho://report/{link_name}"),
                    name=report_config.display_name,
                    description=report_config.description,
                    mimeType="application/json"
                )
            )
        
        return resources
    
    except Exception as e:
        logger.exception("Error in handle_list_resources")
        raise

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> types.TextResourceContents | types.BlobResourceContents:
    """Read data from Zoho Creator based on the resource URI, filtered by whitelist."""
    try:
        logger.info(f"Reading resource: {uri}")
        parsed = urlparse(str(uri))
        
        if parsed.scheme != "zoho":
            raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
        
        full_path = f"{parsed.netloc}{parsed.path}".strip("/")
        path_parts = full_path.split("/")
        
        if not path_parts:
            raise ValueError("Empty resource path")
            
        resource_type = path_parts[0]
        
        # Handle root resources
        if resource_type == "forms":
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "forms": [
                        {
                            "link_name": link_name,
                            "display_name": form.display_name,
                            "description": form.description,
                            "fields": {
                                field_name: field.dict() 
                                for field_name, field in form.fields.items()
                            }
                        }
                        for link_name, form in WHITELISTED_RESOURCES["forms"].items()
                    ]
                }, indent=2)
            )
            
        elif resource_type == "reports":
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "reports": [
                        {
                            "link_name": link_name,
                            "display_name": report.display_name,
                            "description": report.description,
                            "fields": {
                                field_name: field.dict() 
                                for field_name, field in report.fields.items()
                            }
                        }
                        for link_name, report in WHITELISTED_RESOURCES["reports"].items()
                    ]
                }, indent=2)
            )
        
        # Handle specific resources
        if len(path_parts) < 2:
            raise ValueError(f"Missing link name for resource type: {resource_type}")
            
        link_name = path_parts[1]
        
        if resource_type == "form":
            # Check if form is whitelisted
            form_config = WHITELISTED_RESOURCES["forms"].get(link_name)
            if not form_config:
                raise ValueError(f"Form not found or not accessible: {link_name}")
            
            # Get form data from Zoho
            records = await service.get_records(link_name)
            
            # Filter fields based on whitelist
            filtered_records = [
                {
                    field_name: record.data.get(field_name)
                    for field_name in form_config.fields.keys()
                    if field_name in record.data
                }
                for record in records
            ]
            
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "form": {
                        "link_name": link_name,
                        "display_name": form_config.display_name,
                        "description": form_config.description,
                        "fields": {
                            name: field.dict() 
                            for name, field in form_config.fields.items()
                        }
                    },
                    "records": filtered_records
                }, indent=2)
            )
            
        elif resource_type == "report":
            # Check if report is whitelisted
            report_config = WHITELISTED_RESOURCES["reports"].get(link_name)
            if not report_config:
                raise ValueError(f"Report not found or not accessible: {link_name}")
            
            # Get report data from Zoho
            records = await service.get_records(link_name)
            
            # Filter fields based on whitelist
            filtered_records = [
                {
                    field_name: record.data.get(field_name)
                    for field_name in report_config.fields.keys()
                    if field_name in record.data
                }
                for record in records
            ]
            
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "report": {
                        "link_name": link_name,
                        "display_name": report_config.display_name,
                        "description": report_config.description,
                        "fields": {
                            name: field.dict() 
                            for name, field in report_config.fields.items()
                        }
                    },
                    "records": filtered_records
                }, indent=2)
            )
        
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")
            
    except Exception as e:
        logger.exception(f"Error reading resource: {uri}")
        raise

async def main():
    """Main entry point for the server."""
    logger.info("Starting Zoho Creator MCP server...")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        try:
            logger.info("Initializing server connection...")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="scaflog-zoho-mcp-server",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        except Exception as e:
            logger.exception("Error running server")
            raise
        finally:
            logger.info("Shutting down server...")
            await auth.close()
            await service.close()
