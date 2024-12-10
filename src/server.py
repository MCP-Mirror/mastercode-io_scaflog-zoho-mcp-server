# src_scaflog_zoho_mcp_server/server.py

import json
from typing import Dict, List, Optional, Any
from urllib.parse import parse_qs, urlparse
from pydantic import AnyUrl

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .config import load_config
from .auth import ZohoAuth
from .service import ZohoCreatorService

# Create a server instance
server = Server("scaflog-zoho-mcp-server")
config = load_config()
auth = ZohoAuth(config)
service = ZohoCreatorService(auth)

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List all available Zoho Creator forms as resources."""
    forms = await service.list_forms()
    
    resources = []
    resources.append(
        types.Resource(
            uri=AnyUrl("zoho://forms"),
            name="All Forms",
            description="List of all available Zoho Creator forms",
            mimeType="application/json"
        )
    )
    
    for form in forms:
        resources.append(
            types.Resource(
                uri=AnyUrl(f"zoho://forms/{form.link_name}"),
                name=form.display_name,
                description=f"Records from {form.display_name} form",
                mimeType="application/json"
            )
        )
        
        resources.append(
            types.Resource(
                uri=AnyUrl(f"zoho://forms/{form.link_name}/filter/{{criteria}}"),
                name=f"{form.display_name} (Filtered)",
                description=f"Filtered records from {form.display_name} form",
                mimeType="application/json"
            )
        )
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> types.TextResourceContents:
    """Read data from Zoho Creator based on the resource URI."""
    parsed = urlparse(str(uri))
    
    if parsed.scheme != "zoho":
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
    
    path_parts = parsed.path.strip("/").split("/")
    
    if path_parts[0] != "forms":
        raise ValueError(f"Unknown resource type: {path_parts[0]}")
    
    # Handle form list request
    if len(path_parts) == 1:
        forms = await service.list_forms()
        return types.TextResourceContents(
            uri=uri,
            mimeType="application/json",
            text=json.dumps([{
                "link_name": form.link_name,
                "display_name": form.display_name,
                "field_count": len(form.fields)
            } for form in forms], indent=2)
        )
    
    # Get form data
    form_link_name = path_parts[1]
    form = await service.list_forms()
    if not form:
        raise ValueError(f"Form not found: {form_link_name}")
    
    # Handle filtered records
    criteria = None
    if len(path_parts) > 2 and path_parts[2] == "filter":
        criteria = path_parts[3]
    
    # Get records
    records = await service.get_records(form_link_name, criteria)
    
    return types.TextResourceContents(
        uri=uri,
        mimeType="application/json",
        text=json.dumps({
            "form": {
                "link_name": form_link_name,
                "display_name": form.display_name,
                "fields": [field.dict() for field in form.fields]
            },
            "records": [record.dict() for record in records]
        }, indent=2, default=str)
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for Zoho Creator operations."""
    if name == "create-record":
        record = await service.create_record(
            arguments["form_name"],
            arguments["data"]
        )
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "message": "Record created successfully",
                    "record_id": record.id,
                    "created_time": str(record.created_time)
                }, indent=2)
            )
        ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point for the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        try:
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
        finally:
            await auth.close()
            await service.close()
