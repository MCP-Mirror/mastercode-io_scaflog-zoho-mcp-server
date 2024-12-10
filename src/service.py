# src_scaflog_zoho_mcp_server/service.py

from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime

from .models import ZohoForm, ZohoField, ZohoRecord, Cache
from .auth import ZohoAuth
from .config import API_BASE_URL

class ZohoCreatorService:
    """Service for interacting with Zoho Creator API."""
    
    def __init__(self, auth: ZohoAuth):
        self.auth = auth
        self.cache = Cache()
        self._client = httpx.AsyncClient(timeout=30.0)
        self.base_url = API_BASE_URL[auth.config.environment]

    async def list_forms(self, force_refresh: bool = False) -> List[ZohoForm]:
        """Get all available forms."""
        if not force_refresh and not self.cache.needs_refresh():
            return list(self.cache.forms.values())

        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/forms"
        
        async with self._client as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            forms = []
            for form_data in data['forms']:
                fields = await self._get_form_fields(form_data['link_name'], headers)
                form = ZohoForm(
                    link_name=form_data['link_name'],
                    display_name=form_data['display_name'],
                    fields=fields,
                    access_type=form_data.get('access_type', 'read')
                )
                forms.append(form)

            self.cache.update_forms(forms)
            return forms

    async def _get_form_fields(self, form_link_name: str, headers: dict) -> List[ZohoField]:
        """Get fields for a specific form."""
        url = f"{self.base_url}/forms/{form_link_name}/fields"
        
        async with self._client as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            return [
                ZohoField(
                    api_name=field['api_name'],
                    display_name=field['display_name'],
                    field_type=field['type'],
                    max_length=field.get('max_length'),
                    required=field.get('required', False),
                    lookup=field.get('lookup'),
                    choices=field.get('choices')
                )
                for field in data['fields']
            ]

    async def get_records(
        self,
        form_link_name: str,
        criteria: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ZohoRecord]:
        """Get records from a specific form."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/forms/{form_link_name}/records"
        
        params = {}
        if criteria:
            params['criteria'] = criteria
        if limit:
            params['limit'] = limit

        async with self._client as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            return [
                ZohoRecord(
                    id=record['ID'],
                    form_link_name=form_link_name,
                    created_time=datetime.fromisoformat(record['Created_Time'].replace('Z', '+00:00')),
                    modified_time=datetime.fromisoformat(record['Modified_Time'].replace('Z', '+00:00')),
                    data=record
                )
                for record in data['records']
            ]

    async def get_record(
        self,
        form_link_name: str,
        record_id: str
    ) -> ZohoRecord:
        """Get a specific record by ID."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/forms/{form_link_name}/records/{record_id}"
        
        async with self._client as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()

            return ZohoRecord(
                id=record_id,
                form_link_name=form_link_name,
                created_time=datetime.fromisoformat(result['record']['Created_Time'].replace('Z', '+00:00')),
                modified_time=datetime.fromisoformat(result['record']['Modified_Time'].replace('Z', '+00:00')),
                data=result['record']
            )

    async def create_record(
        self,
        form_link_name: str,
        data: Dict[str, Any]
    ) -> ZohoRecord:
        """Create a new record in a form."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/forms/{form_link_name}/records"
        
        async with self._client as client:
            response = await client.post(
                url,
                headers=headers,
                json={"data": data}
            )
            response.raise_for_status()
            result = response.json()

            return ZohoRecord(
                id=result['record']['ID'],
                form_link_name=form_link_name,
                created_time=datetime.fromisoformat(result['record']['Created_Time'].replace('Z', '+00:00')),
                modified_time=datetime.fromisoformat(result['record']['Modified_Time'].replace('Z', '+00:00')),
                data=data
            )

    async def update_record(
        self,
        form_link_name: str,
        record_id: str,
        data: Dict[str, Any]
    ) -> ZohoRecord:
        """Update an existing record in a form."""
        headers = await self.auth.get_authorized_headers()
        url = f"{self.base_url}/forms/{form_link_name}/records/{record_id}"
        
        async with self._client as client:
            response = await client.patch(
                url,
                headers=headers,
                json={"data": data}
            )
            response.raise_for_status()
            result = response.json()

            return ZohoRecord(
                id=record_id,
                form_link_name=form_link_name,
                created_time=datetime.fromisoformat(result['record']['Created_Time'].replace('Z', '+00:00')),
                modified_time=datetime.fromisoformat(result['record']['Modified_Time'].replace('Z', '+00:00')),
                data=data
            )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
        