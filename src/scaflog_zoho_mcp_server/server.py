import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import parse_qs, urlparse
from pydantic import AnyUrl

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .config import load_config, API_BASE_URL
from .auth import ZohoAuth
from .service import ZohoCreatorService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a server instance
logger.info("Initializing server components...")
try:
    server = Server("scaflog-zoho-mcp-server")
    config = load_config()
    auth = ZohoAuth(config)
    service = ZohoCreatorService(auth)
    logger.info("Server components initialized successfully")
except Exception as e:
    logger.exception("Failed to initialize server components")
    raise

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available Zoho Creator forms and reports as resources."""
    logger.debug("Starting handle_list_resources...")

    # create dummy ListResourcesResult with 5 options for test 
    # resources = [
    #     types.Resource(uri=AnyUrl("zoho://form/form1"), name="Form 1", description="Form 1", mimeType="application/json"),
    #     types.Resource(uri=AnyUrl("zoho://form/form2"), name="Form 2", description="Form 2", mimeType="application/json"),
    #     types.Resource(uri=AnyUrl("zoho://form/form3"), name="Form 3", description="Form 3", mimeType="application/json"),
    #     types.Resource(uri=AnyUrl("zoho://form/form4"), name="Form 4", description="Form 4", mimeType="application/json"),
    #     types.Resource(uri=AnyUrl("zoho://form/form5"), name="Form 5", description="Form 5", mimeType="application/json"),
    # ]
    # return resources
    
    # Get cursor from request if provided
    # context = server.request_context
    # cursor = context.params.get("cursor") if hasattr(context, "params") else None
    
    try:
        # Initialize resources list
        resources = []
        
        # Add top-level container resources
        resources.append(
            types.Resource(
                uri=AnyUrl("zoho://forms"),
                name="All Forms",
                description="List of all available Zoho Creator forms",
                mimeType="application/json"
            )
        )
        
        resources.append(
            types.Resource(
                uri=AnyUrl("zoho://reports"),
                name="All Reports", 
                description="List of all available Zoho Creator reports",
                mimeType="application/json"
            )
        )
        
        # Add resources for each form
        forms = await service.list_forms()
        for form in forms:
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"zoho://form/{form.link_name}"),
                    name=form.display_name,
                    description=f"Form definition and fields for {form.display_name}",
                    mimeType="application/json"
                )
            )
        
        # Add resources for each report
        reports = await service.list_reports()
        for report in reports:
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"zoho://report/{report.link_name}"),
                    name=report.display_name,
                    description=f"Records from {report.display_name} report",
                    mimeType="application/json"
                )
            )
        
        return resources
    
    except Exception as e:
        logger.exception("Error in handle_list_resources")
        raise

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> types.TextResourceContents:
    """Read data from Zoho Creator based on the resource URI."""
    try:
        logger.info(f"Reading resource: {uri}")
        parsed = urlparse(str(uri))
        logger.info(f"URI details - scheme: {parsed.scheme}, path: {parsed.path}, netloc: {parsed.netloc}")
        
        if parsed.scheme != "zoho":
            raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
        
        # Combine netloc and path to get the full resource path
        full_path = f"{parsed.netloc}{parsed.path}".strip("/")
        path_parts = [part for part in full_path.split("/") if part]        
        logger.info(f"Path parts: {path_parts}")  # Add this debug line
        
        if not path_parts or not path_parts[0]:
            raise ValueError("Empty resource path")
            
        resource_type = path_parts[0]
        logger.info(f"Resource type: {resource_type}")  # Add this debug line
        
        # Handle root resources first
        if resource_type == "forms":
            # List all forms
            forms = await service.list_forms()
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps([{
                    "link_name": form.link_name,
                    "display_name": form.display_name,
                    "field_count": len(form.fields),
                    "reports": [r.model_dump() for r in form.reports] if hasattr(form, 'reports') else []
                } for form in forms], indent=2)
            )
        
        elif resource_type == "reports":
            # List all reports
            reports = await service.list_reports()
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps([{
                    "link_name": report.link_name,
                    "display_name": report.display_name,
                } for report in reports], indent=2)
            )
        
        # For specific form/report resources, require a link name
        if len(path_parts) < 2:
            raise ValueError(f"Missing link name for resource type: {resource_type}")
            
        link_name = path_parts[1]
        
        if resource_type == "form":
            # Get form fields and metadata
            form = next((f for f in await service.list_forms() if f.link_name == link_name), None)
            if not form:
                raise ValueError(f"Form not found: {link_name}")
                
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "link_name": form.link_name,
                    "display_name": form.display_name,
                    "fields": [field.model_dump() for field in form.fields]
                }, indent=2)
            )
            
        elif resource_type == "report":
            # Handle filtered records for report
            criteria = None
            if len(path_parts) > 3 and path_parts[2] == "filter":
                criteria = path_parts[3]
            
            # Get records through report endpoint
            records = await service.get_records(link_name, criteria)
            
            return types.TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps({
                    "report_name": link_name,
                    "records": [record.model_dump() for record in records]
                }, indent=2, default=str)
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